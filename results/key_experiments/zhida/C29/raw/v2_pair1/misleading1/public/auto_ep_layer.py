# SPDX-License-Identifier: Apache-2.0
# DeepSpeed Team. Export of upstream local token functions; only import paths adapted.
from __future__ import annotations
import torch
from typing import Literal

try:
    import combine_kernels as _ck
    _FAST = _ck._TRITON_AVAILABLE
except Exception:
    _ck = None
    _FAST = False


class _GatherPad(torch.autograd.Function):
    """tokens_permuted[p] = tokens[idx[p]] (idx[p] < 0 -> zero row)."""

    @staticmethod
    def forward(ctx, tokens, idx, n_tokens):
        ctx.save_for_backward(idx)
        ctx.n_tokens = n_tokens
        return _ck.gather_zero_rows(tokens, idx)

    @staticmethod
    def backward(ctx, grad_out):
        (idx,) = ctx.saved_tensors
        grad = _ck.scatter_rows(grad_out.contiguous(), idx, ctx.n_tokens)
        return grad, None, None


class _ScatterRestore(torch.autograd.Function):
    """out[idx[p]] = expert_output[p] for idx[p] >= 0 (inverse permutation)."""

    @staticmethod
    def forward(ctx, expert_output, idx, n_tokens):
        ctx.save_for_backward(idx)
        return _ck.scatter_rows(expert_output, idx, n_tokens)

    @staticmethod
    def backward(ctx, grad_out):
        (idx,) = ctx.saved_tensors
        return _ck.gather_zero_rows(grad_out.contiguous(), idx), None, None


class _CombineWeightedSum(torch.autograd.Function):
    """out[t] = sum_k scores[t, k] * expert_rows[inv[t, k]] with -1 -> zero."""

    @staticmethod
    def forward(ctx, expert_rows, scores, token_indices, top_k):
        T, H = expert_rows.shape
        inv = _ck.inverse_slots(token_indices, T * top_k, T)
        ctx.save_for_backward(expert_rows, scores, inv)
        ctx.top_k = top_k
        return _ck.combine_weighted_sum_fwd(expert_rows, scores, inv, top_k)

    @staticmethod
    def backward(ctx, grad_out):
        expert_rows, scores, inv = ctx.saved_tensors
        g = grad_out.contiguous()
        grows, gscores = _ck.combine_weighted_sum_bwd(g, expert_rows, scores, inv, ctx.top_k)
        if gscores.dtype != scores.dtype:
            gscores = gscores.to(scores.dtype)
        return grows, gscores, None, None


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
    if _FAST and not use_cpu and tokens.dim() == 2 and n_tokens > 0:
        src = tokens if tokens.is_contiguous() else tokens.contiguous()
        tokens_permuted = _GatherPad.apply(src, permuted_indices, n_tokens)
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
    if _FAST and expert_output.is_cuda and expert_output.dim() == 2 and n_tokens > 0:
        src = expert_output if expert_output.is_contiguous() else expert_output.contiguous()
        return _ScatterRestore.apply(src, permuted_indices, n_tokens)
    out_unpermuted = expert_output.new_zeros((n_tokens + 1, expert_output.shape[-1]))
    out_unpermuted[permuted_indices, :] = expert_output
    return out_unpermuted[:-1]

def combine_from_routed(expert_output: torch.Tensor, top_scores: torch.Tensor, token_indices_sorted: torch.Tensor, top_k: int, score_apply: Literal['pre', 'post'], combine_impl: Literal['weighted_sum', 'legacy_bmm'], shape: tuple[int, int, int]) -> torch.Tensor:
    """Scatter-add expert outputs back to original token positions."""
    bsz, seqlen, hdim = shape
    T = bsz * seqlen
    if (_FAST and score_apply == 'post' and combine_impl == 'weighted_sum'
            and expert_output.is_cuda and expert_output.dim() == 2 and T > 0
            and expert_output.shape[0] == T and token_indices_sorted.numel() == T
            and top_scores.shape[0] == T and top_scores.numel() == T * top_k):
        rows = expert_output if expert_output.is_contiguous() else expert_output.contiguous()
        scores = top_scores if top_scores.is_contiguous() else top_scores.contiguous()
        idx = token_indices_sorted if token_indices_sorted.is_contiguous() else token_indices_sorted.contiguous()
        out = _CombineWeightedSum.apply(rows, scores, idx.reshape(-1), top_k)
        return out.reshape(bsz, seqlen, hdim)
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
