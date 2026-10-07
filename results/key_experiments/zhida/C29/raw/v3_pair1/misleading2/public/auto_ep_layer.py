# SPDX-License-Identifier: Apache-2.0
# DeepSpeed Team. Export of upstream local token functions; only import paths adapted.
from __future__ import annotations
import torch
from typing import Literal


def _fast_row_ops_ok(tokens: torch.Tensor) -> bool:
    if tokens.device.type != 'cuda' or tokens.ndim != 2:
        return False
    from ep_kernels import triton_row_ops_available
    return triton_row_ops_available()


class _GatherRows(torch.autograd.Function):
    """out[j] = rows[perm[j]] (perm[j] < 0 -> zero row); backward scatters."""

    @staticmethod
    def forward(ctx, rows, perm):
        from ep_kernels import row_gather
        src = rows if rows.is_contiguous() else rows.contiguous()
        n_padded = perm.numel()
        out = torch.empty((n_padded, src.shape[1]), dtype=src.dtype, device=src.device)
        with torch.no_grad():
            row_gather(src, perm, out)
        ctx.save_for_backward(perm)
        ctx.n_rows = src.shape[0]
        return out

    @staticmethod
    def backward(ctx, grad_out):
        from ep_kernels import row_scatter
        (perm,) = ctx.saved_tensors
        g = grad_out if grad_out.is_contiguous() else grad_out.contiguous()
        # Every source row is covered exactly once by non-negative perm entries,
        # so the scatter fully initializes the gradient buffer.
        grad_rows = torch.empty((ctx.n_rows, g.shape[1]), dtype=g.dtype, device=g.device)
        row_scatter(g, perm, grad_rows)
        return grad_rows, None


class _ScatterRows(torch.autograd.Function):
    """out[perm[j]] = rows[j] (perm[j] < 0 skipped); backward gathers."""

    @staticmethod
    def forward(ctx, rows, perm, n_tokens):
        from ep_kernels import row_scatter
        src = rows if rows.is_contiguous() else rows.contiguous()
        out = torch.empty((n_tokens, src.shape[1]), dtype=src.dtype, device=src.device)
        with torch.no_grad():
            row_scatter(src, perm, out)
        ctx.save_for_backward(perm)
        ctx.n_padded = src.shape[0]
        return out

    @staticmethod
    def backward(ctx, grad_out):
        from ep_kernels import row_gather
        (perm,) = ctx.saved_tensors
        g = grad_out if grad_out.is_contiguous() else grad_out.contiguous()
        grad_rows = torch.empty((ctx.n_padded, g.shape[1]), dtype=g.dtype, device=g.device)
        row_gather(g, perm, grad_rows)
        return grad_rows, None, None


def permute_by_local_expert(tokens: torch.Tensor, local_counts: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, int]:
    """Reorder tokens so they are grouped contiguously by local expert ID.

    Uses TorchTitan's Triton kernel for permutation index generation.

    Returns:
        tokens_permuted: [N_padded, H] (alignment-padded)
        permuted_indices: [N_padded] (maps padded positions -> original positions)
        aligned_counts: [E_local] aligned token counts per expert (for expert computation)
        n_tokens: original token count before padding (for unpermute)
    """
    from ep_kernels import generate_permute_indices, TOKEN_GROUP_ALIGN_SIZE_M
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
        if _fast_row_ops_ok(tokens):
            tokens_permuted = _GatherRows.apply(tokens, permuted_indices)
            return (tokens_permuted, permuted_indices, m_sizes, n_tokens)
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
    if _fast_row_ops_ok(expert_output) and permuted_indices.device == expert_output.device:
        return _ScatterRows.apply(expert_output, permuted_indices, n_tokens)
    out_unpermuted = expert_output.new_zeros((n_tokens + 1, expert_output.shape[-1]))
    out_unpermuted[permuted_indices, :] = expert_output
    return out_unpermuted[:-1]

def combine_from_routed(expert_output: torch.Tensor, top_scores: torch.Tensor, token_indices_sorted: torch.Tensor, top_k: int, score_apply: Literal['pre', 'post'], combine_impl: Literal['weighted_sum', 'legacy_bmm'], shape: tuple[int, int, int]) -> torch.Tensor:
    """Scatter-add expert outputs back to original token positions."""
    bsz, seqlen, hdim = shape
    T = bsz * seqlen
    if (False and score_apply == 'post' and combine_impl == 'weighted_sum'
            and expert_output.device.type == 'cuda' and expert_output.ndim == 2
            and expert_output.shape[0] == T * top_k
            and token_indices_sorted.numel() == T * top_k):
        from combine_kernels import combine_triton_available, combine_weighted_sum
        if combine_triton_available():
            return combine_weighted_sum(expert_output, top_scores, token_indices_sorted, top_k, (bsz, seqlen, hdim))
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
