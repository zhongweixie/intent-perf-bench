# Optional implementation space for local token kernels.
# Fused Triton kernels for the local AutoEP token-movement path.
import torch

_TRITON_AVAILABLE = False
try:
    import triton
    import triton.language as tl

    _TRITON_AVAILABLE = True
except ImportError:
    pass


if _TRITON_AVAILABLE:

    @triton.jit
    def _gather_zero_kernel(
        src_ptr,
        idx_ptr,
        out_ptr,
        H,
        stride_src,
        stride_out,
        BLOCK_H: tl.constexpr,
    ):
        # out[p] = (idx[p] >= 0) ? src[idx[p]] : 0
        p = tl.program_id(0)
        hb = tl.program_id(1)
        j = tl.load(idx_ptr + p)
        offs = hb * BLOCK_H + tl.arange(0, BLOCK_H)
        mask = offs < H
        v = tl.load(src_ptr + j * stride_src + offs, mask=mask & (j >= 0), other=0.0)
        tl.store(out_ptr + p * stride_out + offs, v, mask=mask)

       @triton.jit
    def _scatter_kernel(
        src_ptr,
        idx_ptr,
        out_ptr,
        H,
        stride_src,
        stride_out,
        BLOCK_H: tl.constexpr,
    ):
        # out[idx[p]] = src[p] for idx[p] >= 0 (idx covers every output row once)
        p = tl.program_id(0)
        hb = tl.program_id(1)
        j = tl.load(idx_ptr + p)
        offs = hb * BLOCK_H + tl.arange(0, BLOCK_H)
        mask = offs < H
        v = tl.load(src_ptr + p * stride_src + offs, mask=mask, other=0.0)
        tl.store(out_ptr + j * stride_out + offs, v, mask=mask & (j >= 0))

    @triton.jit
    def _combine_fwd_kernel(
        rows_ptr,
        scores_ptr,
        inv_ptr,
        out_ptr,
        H,
        stride_row,
        stride_out,
        TOP_K: tl.constexpr,
        BLOCK_H: tl.constexpr,
    ):
        # out[t] = sum_k scores[t, k] * rows[inv[t, k]]  (rows[-1] treated as zero)
        t = tl.program_id(0)
        hb = tl.program_id(1)
        offs = hb * BLOCK_H + tl.arange(0, BLOCK_H)
        mask = offs < H
        acc = tl.zeros([BLOCK_H], dtype=tl.float32)
        for k in tl.static_range(TOP_K):
            j = tl.load(inv_ptr + t * TOP_K + k)
            s = tl.load(scores_ptr + t * TOP_K + k).to(tl.float32)
            v = tl.load(rows_ptr + j * stride_row + offs, mask=mask & (j >= 0), other=0.0).to(tl.float32)
            acc += s * v
        tl.store(out_ptr + t * stride_out + offs, acc.to(out_ptr.dtype.element_ty), mask=mask)

    @triton.jit
    def _combine_bwd_kernel(
        go_ptr,
        rows_ptr,
        scores_ptr,
        inv_ptr,
        grows_ptr,
        gscores_ptr,
        H,
        stride_go,
        stride_row,
        stride_grows,
        TOP_K: tl.constexpr,
        BLOCK_H: tl.constexpr,
    ):
        # grows[inv[t,k]] = grad_out[t] * scores[t,k]
        # gscores[t,k] = <grad_out[t], rows[inv[t,k]]>
        t = tl.program_id(0)
        hb = tl.program_id(1)
        offs = hb * BLOCK_H + tl.arange(0, BLOCK_H)
        mask = offs < H
        g = tl.load(go_ptr + t * stride_go + offs, mask=mask, other=0.0).to(tl.float32)
        for k in tl.static_range(TOP_K):
            j = tl.load(inv_ptr + t * TOP_K + k)
            s = tl.load(scores_ptr + t * TOP_K + k).to(tl.float32)
            v = tl.load(rows_ptr + j * stride_row + offs, mask=mask & (j >= 0), other=0.0).to(tl.float32)
            tl.store(
                grows_ptr + j * stride_grows + offs,
                (g * s).to(grows_ptr.dtype.element_ty),
                mask=mask & (j >= 0),
            )
            gs = tl.sum(g * v, axis=0)
            tl.store(gscores_ptr + t * TOP_K + k, gs)


def _block_h(H: int) -> int:
    return max(16, min(1024, triton.next_power_of_2(H)))


def gather_zero_rows(src: torch.Tensor, idx: torch.Tensor) -> torch.Tensor:
    """out[p] = src[idx[p]] with idx[p] < 0 mapping to a zero row."""
    n = idx.numel()
    H = src.shape[-1]
    out = torch.empty((n, H), dtype=src.dtype, device=src.device)
    if n == 0:
        return out
    BLOCK_H = _block_h(H)
    grid = (n, triton.cdiv(H, BLOCK_H))
    _gather_zero_kernel[grid](src, idx, out, H, src.stride(0), out.stride(0), BLOCK_H=BLOCK_H)
    return out


def scatter_rows(src: torch.Tensor, idx: torch.Tensor, n_rows: int) -> torch.Tensor:
    """out[idx[p]] = src[p] for idx[p] >= 0; idx must cover every out row once."""
    H = src.shape[-1]
    out = torch.empty((n_rows, H), dtype=src.dtype, device=src.device)
    if idx.numel() == 0:
        return out
    BLOCK_H = _block_h(H)
    grid = (idx.numel(), triton.cdiv(H, BLOCK_H))
    _scatter_kernel[grid](src, idx, out, H, src.stride(0), out.stride(0), BLOCK_H=BLOCK_H)
    return out


def combine_weighted_sum_fwd(rows: torch.Tensor, scores: torch.Tensor, inv: torch.Tensor, top_k: int) -> torch.Tensor:
    T = rows.shape[0]
    H = rows.shape[1]
    out = torch.empty((T, H), dtype=rows.dtype, device=rows.device)
    if T == 0:
        return out
    BLOCK_H = _block_h(H)
    grid = (T, triton.cdiv(H, BLOCK_H))
    _combine_fwd_kernel[grid](rows, scores, inv, out, H, rows.stride(0), out.stride(0), TOP_K=top_k, BLOCK_H=BLOCK_H)
    return out


def combine_weighted_sum_bwd(grad_out, rows, scores, inv, top_k: int):
    T = rows.shape[0]
    H = rows.shape[1]
    grows = torch.empty((T, H), dtype=rows.dtype, device=rows.device)
    gscores = torch.empty((T, top_k), dtype=torch.float32, device=rows.device)
    if T == 0:
        return grows, gscores
    BLOCK_H = _block_h(H)
    grid = (T, triton.cdiv(H, BLOCK_H))
    _combine_bwd_kernel[grid](
        grad_out, rows, scores, inv, grows, gscores, H,
        grad_out.stride(0), rows.stride(0), grows.stride(0),
        TOP_K=top_k, BLOCK_H=BLOCK_H,
    )
    return grows, gscores


def inverse_slots(token_indices: torch.Tensor, total_slots: int, n_rows: int) -> torch.Tensor:
    """inv[token_indices[j]] = j, elsewhere -1."""
    inv = torch.full((total_slots,), -1, dtype=torch.int32, device=token_indices.device)
    inv[token_indices] = torch.arange(n_rows, dtype=torch.int32, device=token_indices.device)
    return inv
