# Fused local token-movement kernels (Triton) with torch fallbacks.
import torch

_TRITON = False
try:
    import triton
    import triton.language as tl
    _TRITON = True
except ImportError:
    pass

if _TRITON:

    @triton.jit
    def _index_kernel(counts_ptr, perm_ptr, inv_ptr, msizes_ptr, moffs_ptr,
                      R, E, ALIGN: tl.constexpr, RE: tl.constexpr,
                      EP: tl.constexpr, BLOCK: tl.constexpr):
        pid = tl.program_id(0)
        offs = tl.arange(0, RE)
        counts = tl.load(counts_ptr + offs, mask=offs < R * E, other=0).to(tl.int32)
        ep = tl.arange(0, EP)
        tot = tl.zeros((EP,), dtype=tl.int32)
        for r in range(R):
            tot += tl.load(counts_ptr + r * E + ep, mask=ep < E, other=0).to(tl.int32)
        tot = tl.maximum(tot, ALIGN)
        m = (tot + ALIGN - 1) // ALIGN * ALIGN
        moff = tl.cumsum(m, 0) - m
        if pid == 0:
            tl.store(msizes_ptr + ep, m, mask=ep < E)
            tl.store(moffs_ptr + ep, moff + m, mask=ep < E)
        length = tl.load(counts_ptr + pid).to(tl.int32)
        e = pid % E
        start = tl.sum(tl.where(offs < pid, counts, 0), 0)
        prefix = tl.sum(tl.where((offs % E == e) & (offs < pid), counts, 0), 0)
        woff = tl.sum(tl.where(ep == e, moff, 0), 0)
        dest0 = woff + prefix
        for off in range(0, length, BLOCK):
            idx = off + tl.arange(0, BLOCK)
            mk = idx < length
            tl.store(perm_ptr + dest0 + idx, start + idx, mask=mk)
            tl.store(inv_ptr + start + idx, dest0 + idx, mask=mk)
        # last rank fills padding tail with -1
        if pid // E == R - 1:
            mend = tl.sum(tl.where(ep == e, m, 0), 0)
            tail = mend - prefix - length
            tidx = tl.arange(0, 64)
            tl.store(perm_ptr + dest0 + length + tidx, -1 + tl.zeros((64,), tl.int32),
                     mask=tidx < tail)

    @triton.jit
    def _inv_kernel(perm_ptr, inv_ptr, n, BLOCK: tl.constexpr):
        pid = tl.program_id(0)
        offs = pid * BLOCK + tl.arange(0, BLOCK)
        mk = offs < n
        idx = tl.load(perm_ptr + offs, mask=mk, other=-1)
        tl.store(inv_ptr + idx, offs.to(tl.int32), mask=mk & (idx >= 0))

    @triton.jit
    def _gather_kernel(src_ptr, idx_ptr, out_ptr, R, H, BLOCK: tl.constexpr):
        row = tl.program_id(0)
        hc = tl.program_id(1)
        hoff = hc * BLOCK + tl.arange(0, BLOCK)
        hm = hoff < H
        idx = tl.load(idx_ptr + row).to(tl.int64)
        v = tl.load(src_ptr + idx * H + hoff, mask=hm & (idx >= 0), other=0.0)
        tl.store(out_ptr + row.to(tl.int64) * H + hoff, v, mask=hm)

    @triton.jit
    def _invperm_kernel(tis_ptr, invp_ptr, n, BLOCK: tl.constexpr):
        pid = tl.program_id(0)
        offs = pid * BLOCK + tl.arange(0, BLOCK)
        mk = offs < n
        v = tl.load(tis_ptr + offs, mask=mk, other=0)
        tl.store(invp_ptr + v, offs.to(tl.int32), mask=mk)

    @triton.jit
    def _combine_fwd(rows_ptr, scores_ptr, invp_ptr, out_ptr, H,
                     POST: tl.constexpr, TK: tl.constexpr, BLOCK: tl.constexpr):
        t = tl.program_id(0).to(tl.int64)
        hc = tl.program_id(1)
        hoff = hc * BLOCK + tl.arange(0, BLOCK)
        hm = hoff < H
        acc = tl.zeros((BLOCK,), dtype=tl.float32)
        for k in range(TK):
            i = tl.load(invp_ptr + t * TK + k).to(tl.int64)
            v = tl.load(rows_ptr + i * H + hoff, mask=hm & (i >= 0), other=0.0).to(tl.float32)
            if POST:
                s = tl.load(scores_ptr + t * TK + k).to(tl.float32)
                acc += v * s
            else:
                acc += v
        tl.store(out_ptr + t * H + hoff, acc.to(out_ptr.dtype.element_ty), mask=hm)

    @triton.jit
    def _combine_bwd_rows(up_ptr, scores_ptr, tis_ptr, grows_ptr, H,
                          POST: tl.constexpr, TK: tl.constexpr, BLOCK: tl.constexpr):
        i = tl.program_id(0).to(tl.int64)
        hc = tl.program_id(1)
        hoff = hc * BLOCK + tl.arange(0, BLOCK)
        hm = hoff < H
        v = tl.load(tis_ptr + i)
        t = v // TK
        u = tl.load(up_ptr + t * H + hoff, mask=hm, other=0.0).to(tl.float32)
        if POST:
            s = tl.load(scores_ptr + v).to(tl.float32)
            u = u * s
        tl.store(grows_ptr + i * H + hoff, u.to(grows_ptr.dtype.element_ty), mask=hm)

    @triton.jit
    def _combine_bwd_scores(up_ptr, rows_ptr, invp_ptr, gs_ptr, T, H,
                            TK: tl.constexpr, KP: tl.constexpr, BLOCK: tl.constexpr):
        t = tl.program_id(0).to(tl.int64)
        ks = tl.arange(0, KP)
        km = ks < TK
        acc = tl.zeros((KP,), dtype=tl.float32)
        for hc in range(0, H, BLOCK):
            hoff = hc + tl.arange(0, BLOCK)
            hm = hoff < H
            u = tl.load(up_ptr + t * H + hoff, mask=hm, other=0.0).to(tl.float32)
            i = tl.load(invp_ptr + t * TK + ks, mask=km, other=-1).to(tl.int64)
            r = tl.load(rows_ptr + i[:, None] * H + hoff[None, :],
                        mask=km[:, None] & hm[None, :] & (i[:, None] >= 0), other=0.0).to(tl.float32)
            acc += tl.sum(r * u[None, :], axis=1)
        tl.store(gs_ptr + t * TK + ks, acc, mask=km)


def _pow2(n):
    p = 1
    while p < n:
        p *= 2
    return p


def fast_indices(counts_flat, R, E, max_len, alignment, n_rows, device):
    """Fused replacement for generate_permute_indices on CUDA. Also returns inverse."""
    perm = torch.empty((max_len,), dtype=torch.int32, device=device)
    inv = torch.empty((n_rows,), dtype=torch.int32, device=device)
    m_sizes = torch.empty((E,), dtype=torch.int32, device=device)
    m_offsets = torch.empty((E,), dtype=torch.int32, device=device)
    _index_kernel[(R * E,)](counts_flat, perm, inv, m_sizes, m_offsets, R, E,
                            ALIGN=alignment, RE=_pow2(R * E), EP=_pow2(E), BLOCK=512)
    return perm, inv, m_sizes, m_offsets


def inverse_of_perm(perm, n_rows, device):
    inv = torch.empty((n_rows,), dtype=torch.int32, device=device)
    _inv_kernel[(triton.cdiv(perm.numel(), 512),)](perm, inv, perm.numel(), BLOCK=512)
    return inv


class GatherPad(torch.autograd.Function):
    """out[p] = src[idx[p]] for idx[p]>=0 else 0; backward gathers via inv."""

    @staticmethod
    def forward(ctx, src, idx, inv, out_rows):
        n, H = src.shape
        BLOCK = min(2048, _pow2(H))
        out = torch.empty((out_rows, H), dtype=src.dtype, device=src.device)
        _gather_kernel[(out_rows, triton.cdiv(H, BLOCK))](src, idx, out, out_rows, H, BLOCK=BLOCK)
        ctx.save_for_backward(inv)
        ctx.n = n
        ctx.H = H
        ctx.dtype = src.dtype
        ctx.device = src.device
        return out

    @staticmethod
    def backward(ctx, grad_out):
        (inv,) = ctx.saved_tensors
        H, n = ctx.H, ctx.n
        g = grad_out.contiguous()
        grad = torch.empty((n, H), dtype=ctx.dtype, device=ctx.device)
        BLOCK = min(2048, _pow2(H))
        _gather_kernel[(n, triton.cdiv(H, BLOCK))](g, inv, grad, n, H, BLOCK=BLOCK)
        return grad, None, None, None


class Unpermute(torch.autograd.Function):
    """out[i] = src[inv[i]] (i<n); backward scatters via perm (pad->0)."""

    @staticmethod
    def forward(ctx, src, perm, n_rows):
        padded, H = src.shape
        inv = inverse_of_perm(perm, n_rows, src.device)
        out = torch.empty((n_rows, H), dtype=src.dtype, device=src.device)
        BLOCK = min(2048, _pow2(H))
        _gather_kernel[(n_rows, triton.cdiv(H, BLOCK))](src, inv, out, n_rows, H, BLOCK=BLOCK)
        ctx.save_for_backward(perm)
        ctx.padded = padded
        ctx.H = H
        ctx.dtype = src.dtype
        ctx.device = src.device
        return out

    @staticmethod
    def backward(ctx, grad_out):
        (perm,) = ctx.saved_tensors
        H, padded = ctx.H, ctx.padded
        g = grad_out.contiguous()
        grad = torch.empty((padded, H), dtype=ctx.dtype, device=ctx.device)
        BLOCK = min(2048, _pow2(H))
        _gather_kernel[(padded, triton.cdiv(H, BLOCK))](g, perm, grad, padded, H, BLOCK=BLOCK)
        return grad, None, None


class Combine(torch.autograd.Function):
    """out[t] = sum_k (score[t,k] *) rows[invperm[t*top_k+k]] with fp32 accum."""

    @staticmethod
    def forward(ctx, rows, scores, tis, top_k, shape):
        n, H = rows.shape
        T = shape[0] * shape[1]
        invp = torch.full((T * top_k,), -1, dtype=torch.int32, device=rows.device)
        _invperm_kernel[(triton.cdiv(n, 1024),)](tis, invp, n, BLOCK=1024)
        out = torch.empty((T, H), dtype=rows.dtype, device=rows.device)
        BLOCK = min(1024, _pow2(H))
        post = scores is not None
        _combine_fwd[(T, triton.cdiv(H, BLOCK))](
            rows, scores if post else rows, invp, out, H,
            POST=post, TK=top_k, BLOCK=BLOCK)
        ctx.save_for_backward(rows, scores, tis, invp)
        ctx.top_k = top_k
        ctx.T = T
        ctx.H = H
        return out.view(shape)

    @staticmethod
    def backward(ctx, grad_out):
        rows, scores, tis, invp = ctx.saved_tensors
        top_k, T, H = ctx.top_k, ctx.T, ctx.H
        n = rows.shape[0]
        up = grad_out.contiguous().view(T, H)
        post = scores is not None
        grad_rows = torch.empty_like(rows)
        BLOCK = min(1024, _pow2(H))
        _combine_bwd_rows[(n, triton.cdiv(H, BLOCK))](
            up, scores if post else up, tis, grad_rows, H,
            POST=post, TK=top_k, BLOCK=BLOCK)
        grad_scores = None
        if post:
            gs = torch.empty((T, top_k), dtype=torch.float32, device=rows.device)
            _combine_bwd_scores[(T,)](up, rows, invp, gs, T, H,
                                      TK=top_k, KP=_pow2(top_k), BLOCK=256)
            grad_scores = gs.to(scores.dtype).view(scores.shape)
        return grad_rows, grad_scores, None, None, None


def triton_available():
    return _TRITON
