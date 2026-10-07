# Optional implementation space for local token kernels.
import torch

_TRITON_AVAILABLE = False
try:
    import triton
    import triton.language as tl
    _TRITON_AVAILABLE = True
except ImportError:
    pass

_BLOCK_H = 1024

if _TRITON_AVAILABLE:

    @triton.jit
    def _gather_zero_kernel(SRC, IDX, OUT, H: tl.constexpr, BLOCK_H: tl.constexpr):
        # OUT[j] = (IDX[j] >= 0) ? SRC[IDX[j]] : 0
        j = tl.program_id(0).to(tl.int64)
        hb = tl.program_id(1)
        offs = hb * BLOCK_H + tl.arange(0, BLOCK_H)
        hmask = offs < H
        i = tl.load(IDX + j)
        valid = i >= 0
        ii = tl.where(valid, i, 0).to(tl.int64)
        v = tl.load(SRC + ii * H + offs, mask=hmask & valid, other=0.0)
        tl.store(OUT + j * H + offs, v, mask=hmask)

    @triton.jit
    def _scatter_kernel(SRC, IDX, DST, H: tl.constexpr, BLOCK_H: tl.constexpr):
        # DST[IDX[j]] = SRC[j] for valid (>=0) indices; unique indices assumed.
        j = tl.program_id(0).to(tl.int64)
        hb = tl.program_id(1)
        offs = hb * BLOCK_H + tl.arange(0, BLOCK_H)
        hmask = offs < H
        i = tl.load(IDX + j)
        valid = i >= 0
        v = tl.load(SRC + j * H + offs, mask=hmask, other=0.0)
        tl.store(DST + i.to(tl.int64) * H + offs, v, mask=hmask & valid)

    @triton.jit
    def _inverse_kernel(IDX, INV, n, BLOCK: tl.constexpr):
        pid = tl.program_id(0).to(tl.int64)
        offs = pid * BLOCK + tl.arange(0, BLOCK)
        mask = offs < n
        j = tl.load(IDX + offs, mask=mask, other=0).to(tl.int64)
        tl.store(INV + j, offs.to(tl.int32), mask=mask)

    @triton.jit
    def _combine_fwd_kernel(E, INV, S, OUT, H: tl.constexpr,
                            TOP_K: tl.constexpr, BLOCK_H: tl.constexpr):
        t = tl.program_id(0).to(tl.int64)
        hb = tl.program_id(1)
        offs = hb * BLOCK_H + tl.arange(0, BLOCK_H)
        hmask = offs < H
        acc = tl.zeros((BLOCK_H,), dtype=tl.float32)
        for k in tl.static_range(TOP_K):
            row = tl.load(INV + t * TOP_K + k).to(tl.int64)
            s = tl.load(S + t * TOP_K + k).to(tl.float32)
            e = tl.load(E + row * H + offs, mask=hmask, other=0.0).to(tl.float32)
            acc += e * s
        tl.store(OUT + t * H + offs, acc.to(OUT.dtype.element_ty), mask=hmask)

    @triton.jit
    def _combine_bwd_e_kernel(UP, S, IDX, GE, H: tl.constexpr,
                              TOP_K: tl.constexpr, BLOCK_H: tl.constexpr):
        i = tl.program_id(0).to(tl.int64)
        hb = tl.program_id(1)
        j = tl.load(IDX + i).to(tl.int64)
        t = j // TOP_K
        s = tl.load(S + j).to(tl.float32)
        offs = hb * BLOCK_H + tl.arange(0, BLOCK_H)
        hmask = offs < H
        up = tl.load(UP + t * H + offs, mask=hmask, other=0.0).to(tl.float32)
        tl.store(GE + i * H + offs, (up * s).to(GE.dtype.element_ty), mask=hmask)

    @triton.jit
    def _combine_bwd_s_kernel(UP, E, INV, GS, H: tl.constexpr,
                              TOP_K: tl.constexpr, TKP: tl.constexpr,
                              BLOCK_H: tl.constexpr):
        t = tl.program_id(0).to(tl.int64)
        kk = tl.arange(0, TKP)
        accs = tl.zeros((TKP,), dtype=tl.float32)
        for hb in range(0, H, BLOCK_H):
            offs = hb + tl.arange(0, BLOCK_H)
            hmask = offs < H
            up = tl.load(UP + t * H + offs, mask=hmask, other=0.0).to(tl.float32)
            for k in tl.static_range(TOP_K):
                row = tl.load(INV + t * TOP_K + k).to(tl.int64)
                e = tl.load(E + row * H + offs, mask=hmask, other=0.0).to(tl.float32)
                accs += tl.where(kk == k, tl.sum(up * e), 0.0)
        tl.store(GS + t * TOP_K + kk, accs.to(GS.dtype.element_ty), mask=kk < TOP_K)


def _hgrid(H):
    return (H + _BLOCK_H - 1) // _BLOCK_H


class GatherZero(torch.autograd.Function):
    """out[j] = src[idx[j]] for idx[j] >= 0 else 0. Backward scatters (unique)."""

    @staticmethod
    def forward(ctx, src, idx):
        n, H = src.shape
        out = src.new_empty((idx.shape[0], H))
        _gather_zero_kernel[(idx.shape[0], _hgrid(H))](
            src, idx, out, H=H, BLOCK_H=_BLOCK_H, num_warps=4)
        ctx.save_for_backward(idx)
        ctx.n = n
        return out

    @staticmethod
    def backward(ctx, go):
        (idx,) = ctx.saved_tensors
        H = go.shape[1]
        go = go.contiguous()
        grad_src = go.new_empty((ctx.n, H))
        _scatter_kernel[(idx.shape[0], _hgrid(H))](
            go, idx, grad_src, H=H, BLOCK_H=_BLOCK_H, num_warps=4)
        return grad_src, None


class ScatterDrop(torch.autograd.Function):
    """out[idx[j]] = src[j] for valid idx, dropping invalid slots. Backward gathers."""

    @staticmethod
    def forward(ctx, src, idx, n):
        H = src.shape[1]
        out = src.new_empty((n, H))
        _scatter_kernel[(idx.shape[0], _hgrid(H))](
            src, idx, out, H=H, BLOCK_H=_BLOCK_H, num_warps=4)
        ctx.save_for_backward(idx)
        return out

    @staticmethod
    def backward(ctx, go):
        (idx,) = ctx.saved_tensors
        H = go.shape[1]
        go = go.contiguous()
        grad_src = go.new_empty((idx.shape[0], H))
        _gather_zero_kernel[(idx.shape[0], _hgrid(H))](
            go, idx, grad_src, H=H, BLOCK_H=_BLOCK_H, num_warps=4)
        return grad_src, None, None


class CombinePost(torch.autograd.Function):
    """Fused scatter + weighted top-k sum for score_apply='post'/'weighted_sum'."""

    @staticmethod
    def forward(ctx, expert_output, top_scores, token_indices, top_k, shape):
        bsz, seqlen, hdim = shape
        T = bsz * seqlen
        n, H = expert_output.shape
        dev = expert_output.device
        inv = torch.empty(n, dtype=torch.int32, device=dev)
        _inverse_kernel[((n + 255) // 256,)](token_indices, inv, n, BLOCK=256)
        out = expert_output.new_empty((T, H))
        _combine_fwd_kernel[(T, _hgrid(H))](
            expert_output, inv, top_scores, out, H=H, TOP_K=top_k,
            BLOCK_H=_BLOCK_H, num_warps=4)
        ctx.save_for_backward(expert_output, top_scores, token_indices, inv)
        ctx.top_k = top_k
        return out.reshape(bsz, seqlen, hdim)

    @staticmethod
    def backward(ctx, grad_out):
        expert_output, top_scores, token_indices, inv = ctx.saved_tensors
        top_k = ctx.top_k
        n, H = expert_output.shape
        T = top_scores.shape[0]
        go = grad_out.reshape(T, H).contiguous()
        grad_e = expert_output.new_empty((n, H))
        _combine_bwd_e_kernel[(n, _hgrid(H))](
            go, top_scores, token_indices, grad_e, H=H, TOP_K=top_k,
            BLOCK_H=_BLOCK_H, num_warps=4)
        grad_s = torch.empty_like(top_scores)
        tkp = 1 << (top_k - 1).bit_length()
        bh = min(_BLOCK_H, 1 << (H - 1).bit_length())
        _combine_bwd_s_kernel[(T,)](
            go, expert_output, inv, grad_s, H=H, TOP_K=top_k, TKP=tkp,
            BLOCK_H=bh, num_warps=4)
        return grad_e, grad_s, None, None, None


def combine_post_triton(expert_output, top_scores, token_indices, top_k, shape):
    return CombinePost.apply(expert_output, top_scores, token_indices, top_k, shape)


def gather_zero_triton(src, idx):
    return GatherZero.apply(src, idx)


def scatter_drop_triton(src, idx, n):
    return ScatterDrop.apply(src, idx, n)
