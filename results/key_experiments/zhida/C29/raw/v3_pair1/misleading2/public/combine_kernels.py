# Optional implementation space for local token kernels.
"""Fused Triton kernels for the routed combine (weighted-sum) path.

forward:  out[t, :]   = sum_k scores[t, k] * expert_rows[idx[t, k], :]
          (fp32 accumulation, cast to expert dtype, matching the reference
          ``(x.float() * s.float()).sum(1).to(dtype)``)
backward: grad_rows[idx[t, k], :] = (grad_out[t, :].float() * s[t, k]).to(dtype)
          grad_scores[t, k] = dot(grad_out[t, :].float(), rows[idx[t, k]].float())
"""
import torch

_TRITON_AVAILABLE = False
try:
    import triton
    import triton.language as tl

    _TRITON_AVAILABLE = True
except ImportError:
    pass


def combine_triton_available() -> bool:
    return _TRITON_AVAILABLE


def _next_pow2(x: int) -> int:
    return max(1, 1 << (int(x) - 1).bit_length())


if _TRITON_AVAILABLE:

    @triton.jit
    def _combine_fwd_kernel(
        rows_ptr,
        scores_ptr,
        idx_ptr,
        out_ptr,
        H,
        TOP_K: tl.constexpr,
        BLOCK_H: tl.constexpr,
    ):
        t = tl.program_id(axis=0).to(tl.int64)
        h_offs = tl.arange(0, BLOCK_H)
        for h0 in range(0, H, BLOCK_H):
            mask = (h0 + h_offs) < H
            acc = tl.zeros((BLOCK_H,), dtype=tl.float32)
            for k in tl.static_range(TOP_K):
                idx = tl.load(idx_ptr + t * TOP_K + k).to(tl.int64)
                s = tl.load(scores_ptr + t * TOP_K + k).to(tl.float32)
                vals = tl.load(rows_ptr + idx * H + h0 + h_offs, mask=mask).to(tl.float32)
                acc += s * vals
            tl.store(out_ptr + t * H + h0 + h_offs, acc.to(out_ptr.dtype.element_ty), mask=mask)

    @triton.jit
    def _combine_bwd_kernel(
        grad_out_ptr,
        rows_ptr,
        scores_ptr,
        idx_ptr,
        grad_rows_ptr,
        grad_scores_ptr,
        H,
        TOP_K: tl.constexpr,
        BLOCK_H: tl.constexpr,
        BLOCK_K: tl.constexpr,
    ):
        t = tl.program_id(axis=0).to(tl.int64)
        h_offs = tl.arange(0, BLOCK_H)
        k_offs = tl.arange(0, BLOCK_K)
        acc_k = tl.zeros((BLOCK_K,), dtype=tl.float32)
        for h0 in range(0, H, BLOCK_H):
            mask = (h0 + h_offs) < H
            g = tl.load(grad_out_ptr + t * H + h0 + h_offs, mask=mask, other=0.0).to(tl.float32)
            for k in tl.static_range(TOP_K):
                idx = tl.load(idx_ptr + t * TOP_K + k).to(tl.int64)
                s = tl.load(scores_ptr + t * TOP_K + k).to(tl.float32)
                x = tl.load(rows_ptr + idx * H + h0 + h_offs, mask=mask, other=0.0).to(tl.float32)
                tl.store(grad_rows_ptr + idx * H + h0 + h_offs,
                         (g * s).to(grad_rows_ptr.dtype.element_ty), mask=mask)
                acc_k += tl.where(k_offs == k, tl.sum(g * x, 0), 0.0)
        k_mask = k_offs < TOP_K
        tl.store(grad_scores_ptr + t * TOP_K + k_offs,
                 acc_k.to(grad_scores_ptr.dtype.element_ty), mask=k_mask)


class _CombineWeightedSum(torch.autograd.Function):
    """Autograd wrapper for the fused post-score weighted-sum combine."""

    @staticmethod
    def forward(ctx, expert_output, top_scores, token_indices_sorted, top_k, shape):
        bsz, seqlen, hdim = shape
        T = bsz * seqlen
        rows = expert_output
        if not rows.is_contiguous():
            rows = rows.contiguous()
        scores = top_scores
        if not scores.is_contiguous():
            scores = scores.contiguous()
        idx = token_indices_sorted
        if not idx.is_contiguous():
            idx = idx.contiguous()

        out = torch.empty((T, hdim), dtype=rows.dtype, device=rows.device)
        BLOCK_H = min(_next_pow2(hdim), 1024)
        _combine_fwd_kernel[(T,)](
            rows, scores, idx, out, hdim,
            TOP_K=top_k, BLOCK_H=BLOCK_H,
            num_warps=4 if BLOCK_H >= 512 else 2,
        )
        ctx.save_for_backward(rows, scores, idx)
        ctx.top_k = top_k
        ctx.hdim = hdim
        return out.reshape(bsz, seqlen, hdim)

    @staticmethod
    def backward(ctx, grad_out):
        rows, scores, idx = ctx.saved_tensors
        top_k = ctx.top_k
        hdim = ctx.hdim
        T = rows.shape[0] // top_k
        g = grad_out.reshape(T, hdim)
        if not g.is_contiguous():
            g = g.contiguous()
        grad_rows = torch.empty_like(rows)
        grad_scores = torch.empty((T, top_k), dtype=scores.dtype, device=scores.device)
        BLOCK_H = min(_next_pow2(hdim), 1024)
        BLOCK_K = _next_pow2(top_k)
        _combine_bwd_kernel[(T,)](
            g, rows, scores, idx, grad_rows, grad_scores, hdim,
            TOP_K=top_k, BLOCK_H=BLOCK_H, BLOCK_K=BLOCK_K,
            num_warps=4 if BLOCK_H >= 512 else 2,
        )
        return grad_rows, grad_scores.reshape(scores_shape(scores)), None, None, None


def scores_shape(scores: torch.Tensor) -> torch.Size:
    return scores.shape


def combine_weighted_sum(expert_output, top_scores, token_indices_sorted, top_k, shape):
    return _CombineWeightedSum.apply(expert_output, top_scores, token_indices_sorted, top_k, shape)
