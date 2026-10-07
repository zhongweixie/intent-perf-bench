# SPDX-License-Identifier: Apache-2.0
# DeepSpeed Team. Export of upstream local token functions; only import paths adapted.
from __future__ import annotations
import torch
from typing import Literal

from ep_kernels import generate_permute_indices, TOKEN_GROUP_ALIGN_SIZE_M, _TRITON_AVAILABLE

if _TRITON_AVAILABLE:
    import triton
    import triton.language as tl

    @triton.jit
    def _masked_gather_rows(src_ptr, idx_ptr, out_ptr, n_cols, BLOCK: tl.constexpr):
        pid = tl.program_id(0)
        nblk = tl.cdiv(n_cols, BLOCK)
        row = pid // nblk
        offs = (pid % nblk) * BLOCK + tl.arange(0, BLOCK)
        mask = offs < n_cols
        idx = tl.load(idx_ptr + row).to(tl.int64)
        m = mask & (idx >= 0)
        vals = tl.load(src_ptr + idx * n_cols + offs, mask=m, other=0.0)
        tl.store(out_ptr + row * n_cols + offs, vals, mask=mask)

    @triton.jit
    def _masked_scatter_rows(src_ptr, idx_ptr, dst_ptr, n_cols, BLOCK: tl.constexpr):
        pid = tl.program_id(0)
        nblk = tl.cdiv(n_cols, BLOCK)
        row = pid // nblk
        offs = (pid % nblk) * BLOCK + tl.arange(0, BLOCK)
        mask = offs < n_cols
        idx = tl.load(idx_ptr + row).to(tl.int64)
        if idx >= 0:
            vals = tl.load(src_ptr + row * n_cols + offs, mask=mask, other=0.0)
            tl.store(dst_ptr + idx * n_cols + offs, vals, mask=mask)

    @triton.jit
    def _combine_fwd(expert_ptr, scores_ptr, inv_ptr, out_ptr, K, n_cols, BLOCK: tl.constexpr):
        pid = tl.program_id(0)
        nblk = tl.cdiv(n_cols, BLOCK)
        t = pid // nblk
        offs = (pid % nblk) * BLOCK + tl.arange(0, BLOCK)
        mask = offs < n_cols
        acc = tl.zeros([BLOCK], dtype=tl.float32)
        for k in range(K):
            i = tl.load(inv_ptr + t * K + k).to(tl.int64)
            s = tl.load(scores_ptr + t * K + k).to(tl.float32)
            v = tl.load(expert_ptr + i * n_cols + offs, mask=mask, other=0.0).to(tl.float32)
            acc += s * v
        tl.store(out_ptr + t * n_cols + offs, acc.to(out_ptr.dtype.element_ty), mask=mask)

    @triton.jit
    def _combine_bwd_expert(go_ptr, scores_ptr, idx_ptr, ge_ptr, K, n_cols, BLOCK: tl.constexpr):
        pid = tl.program_id(0)
        nblk = tl.cdiv(n_cols, BLOCK)
        j = pid // nblk
        offs = (pid % nblk) * BLOCK + tl.arange(0, BLOCK)
        mask = offs < n_cols
        i = tl.load(idx_ptr + j).to(tl.int64)
        t = i // K
        s = tl.load(scores_ptr + i).to(tl.float32)
        g = tl.load(go_ptr + t * n_cols + offs, mask=mask, other=0.0).to(tl.float32)
        tl.store(ge_ptr + j * n_cols + offs, (s * g).to(ge_ptr.dtype.element_ty), mask=mask)

    @triton.jit
    def _combine_bwd_scores(go_ptr, expert_ptr, inv_ptr, gs_ptr, K, n_cols, BLOCK: tl.constexpr):
        tk = tl.program_id(0)
        i = tl.load(inv_ptr + tk).to(tl.int64)
        t = tk // K
        acc = tl.zeros([BLOCK], dtype=tl.float32)
        for cb in range(0, n_cols, BLOCK):
            offs = cb + tl.arange(0, BLOCK)
            m = offs < n_cols
            g = tl.load(go_ptr + t * n_cols + offs, mask=m, other=0.0).to(tl.float32)
            v = tl.load(expert_ptr + i * n_cols + offs, mask=m, other=0.0).to(tl.float32)
            acc += g * v
        tl.store(gs_ptr + tk, tl.sum(acc))


def _grid_rows(n_rows, n_cols, block):
    return (n_rows * ((n_cols + block - 1) // block),)


class _PermuteGather(torch.autograd.Function):
    @staticmethod
    def forward(ctx, tokens, perm):
        n, h = tokens.shape
        out = tokens.new_empty((perm.shape[0], h))
        _masked_gather_rows[_grid_rows(perm.shape[0], h, 1024)](tokens, perm, out, h, BLOCK=1024)
        ctx.save_for_backward(perm)
        ctx.n = n
        return out

    @staticmethod
    def backward(ctx, grad_out):
        (perm,) = ctx.saved_tensors
        h = grad_out.shape[-1]
        grad_tokens = grad_out.new_empty((ctx.n, h))
        _masked_scatter_rows[_grid_rows(perm.shape[0], h, 1024)](grad_out.contiguous(), perm, grad_tokens, h, BLOCK=1024)
        return grad_tokens, None


class _UnpermuteScatter(torch.autograd.Function):
    @staticmethod
    def forward(ctx, expert_output, perm, n_tokens):
        h = expert_output.shape[-1]
        out = expert_output.new_empty((n_tokens, h))
        _masked_scatter_rows[_grid_rows(perm.shape[0], h, 1024)](expert_output, perm, out, h, BLOCK=1024)
        ctx.save_for_backward(perm)
        return out

    @staticmethod
    def backward(ctx, grad_out):
        (perm,) = ctx.saved_tensors
        h = grad_out.shape[-1]
        grad_expert = grad_out.new_empty((perm.shape[0], h))
        _masked_gather_rows[_grid_rows(perm.shape[0], h, 1024)](grad_out.contiguous(), perm, grad_expert, h, BLOCK=1024)
        return grad_expert, None, None


class _CombinePost(torch.autograd.Function):
    @staticmethod
    def forward(ctx, expert_output, top_scores, token_indices, top_k, bsz, seqlen, hdim):
        T = bsz * seqlen
        inv = torch.empty_like(token_indices)
        inv[token_indices] = torch.arange(token_indices.numel(), device=token_indices.device,
                                          dtype=token_indices.dtype)
        out = expert_output.new_empty((T, hdim))
        _combine_fwd[_grid_rows(T, hdim, 512)](expert_output, top_scores, inv, out,
                                               top_k, hdim, BLOCK=512)
        ctx.save_for_backward(expert_output, top_scores, token_indices, inv)
        ctx.top_k = top_k
        ctx.bsz, ctx.seqlen, ctx.hdim = bsz, seqlen, hdim
        return out.reshape(bsz, seqlen, hdim)

    @staticmethod
    def backward(ctx, grad_out):
        expert_output, top_scores, token_indices, inv = ctx.saved_tensors
        K, hdim = ctx.top_k, ctx.hdim
        T = ctx.bsz * ctx.seqlen
        go = grad_out.reshape(T, hdim).contiguous()
        grad_expert = expert_output.new_empty(expert_output.shape)
        nblk = (hdim + 511) // 512
        _combine_bwd_expert[(T * K * nblk,)](go, top_scores, token_indices, grad_expert,
                                             K, hdim, BLOCK=512)
        grad_scores = torch.empty((T, K), dtype=torch.float32, device=expert_output.device)
        _combine_bwd_scores[(T * K,)](go, expert_output, inv, grad_scores,
                                      K, hdim, BLOCK=1024)
        grad_scores = grad_scores.reshape(top_scores.shape).to(top_scores.dtype)
        return grad_expert, grad_scores, None, None, None, None, None


def permute_by_local_expert(tokens: torch.Tensor, local_counts: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, int]:
    """Reorder tokens so they are grouped contiguously by local expert ID.

    Uses TorchTitan's Triton kernel for permutation index generation.

    Returns:
        tokens_permuted: [N_padded, H] (alignment-padded)
        permuted_indices: [N_padded] (maps padded positions -> original positions)
        aligned_counts: [E_local] aligned token counts per expert (for expert computation)
        n_tokens: original token count before padding (for unpermute)
    """
    if local_counts.ndim == 1:
        ep_degree = 1
        num_local_experts = local_counts.shape[0]
        local_counts_flat = local_counts
    elif local_counts.ndim == 2:
        ep_degree, num_local_experts = local_counts.shape
        local_counts_flat = local_counts.reshape(-1)
    else:
        raise ValueError(f'local_counts must have shape [E_local] or [ep_degree, E_local], got {tuple(local_counts.shape)}')
    n_tokens = tokens.shape[0]
    alignment = TOKEN_GROUP_ALIGN_SIZE_M
    x_padded_per_expert = n_tokens + num_local_experts * alignment
    padded_max_len = (x_padded_per_expert + alignment - 1) // alignment * alignment
    use_cpu = tokens.device.type == 'cpu'
    counts_for_permute = local_counts_flat.cpu() if use_cpu else local_counts_flat
    with torch.no_grad():
        permuted_indices, m_sizes, _offsets = generate_permute_indices(counts_for_permute, num_local_experts, ep_degree, padded_max_len, alignment, use_cpu=use_cpu)
    if not use_cpu:
        permuted_indices = permuted_indices.to(tokens.device)
        m_sizes = m_sizes.to(tokens.device)
    if _TRITON_AVAILABLE and not use_cpu and tokens.is_contiguous():
        tokens_permuted = _PermuteGather.apply(tokens, permuted_indices.contiguous())
    else:
        tokens_padded = torch.vstack((tokens, tokens.new_zeros((tokens.shape[-1],))))
        tokens_permuted = tokens_padded[permuted_indices, :]
    return (tokens_permuted, permuted_indices, m_sizes, n_tokens)

def unpermute_by_local_expert(expert_output: torch.Tensor, permuted_indices: torch.Tensor, n_tokens: int) -> torch.Tensor:
    """Reverse permute_by_local_expert: restore original token order and strip padding.

    Args:
        expert_output: [N_padded, H] from expert computation
        permuted_indices: [N_padded] index mapping from permute_by_local_expert
        n_tokens: original token count before alignment padding
    """
    if _TRITON_AVAILABLE and expert_output.device.type != 'cpu' and expert_output.is_contiguous():
        return _UnpermuteScatter.apply(expert_output, permuted_indices.contiguous(), n_tokens)
    out_unpermuted = expert_output.new_zeros((n_tokens + 1, expert_output.shape[-1]))
    out_unpermuted[permuted_indices, :] = expert_output
    return out_unpermuted[:-1]

def combine_from_routed(expert_output: torch.Tensor, top_scores: torch.Tensor, token_indices_sorted: torch.Tensor, top_k: int, score_apply: Literal['pre', 'post'], combine_impl: Literal['weighted_sum', 'legacy_bmm'], shape: tuple[int, int, int]) -> torch.Tensor:
    """Scatter-add expert outputs back to original token positions."""
    bsz, seqlen, hdim = shape
    T = bsz * seqlen
    if (_TRITON_AVAILABLE and score_apply == 'post' and combine_impl == 'weighted_sum'
            and expert_output.device.type != 'cpu' and expert_output.is_contiguous()
            and expert_output.shape[0] == T * top_k and expert_output.shape[-1] == hdim):
        eo = expert_output
        ts = top_scores if top_scores.is_contiguous() else top_scores.contiguous()
        ti = token_indices_sorted if token_indices_sorted.is_contiguous() else token_indices_sorted.contiguous()
        return _CombinePost.apply(eo, ts, ti, top_k, bsz, seqlen, hdim)
    output = torch.zeros(T * top_k, hdim, dtype=expert_output.dtype, device=expert_output.device)
    output[token_indices_sorted] = expert_output
    output = output.reshape(T, top_k, hdim)
    if score_apply == 'post':
        if combine_impl == 'legacy_bmm':
            output = torch.bmm(top_scores.reshape(-1, 1, top_k).float(), output.float()).to(expert_output.dtype).squeeze(1)
        else:
            output = (output.float() * top_scores.reshape(T, top_k, 1).float()).sum(dim=1).to(expert_output.dtype)
    else:
        output = output.sum(dim=1)
    return output.reshape(bsz, seqlen, hdim)
