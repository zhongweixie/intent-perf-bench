# SPDX-License-Identifier: Apache-2.0
# DeepSpeed Team. Export of upstream local token functions; only import paths adapted.
from __future__ import annotations
import torch
from typing import Literal

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
    out_unpermuted = expert_output.new_zeros((n_tokens + 1, expert_output.shape[-1]))
    out_unpermuted[permuted_indices, :] = expert_output
    return out_unpermuted[:-1]

def combine_from_routed(expert_output: torch.Tensor, top_scores: torch.Tensor, token_indices_sorted: torch.Tensor, top_k: int, score_apply: Literal['pre', 'post'], combine_impl: Literal['weighted_sum', 'legacy_bmm'], shape: tuple[int, int, int]) -> torch.Tensor:
    """Scatter-add expert outputs back to original token positions."""
    bsz, seqlen, hdim = shape
    T = bsz * seqlen
    idx = token_indices_sorted
    if idx.dtype != torch.int64:
        idx = idx.long()
    idx = idx.reshape(-1)
    t_idx = torch.div(idx, top_k, rounding_mode='floor')
    # Accumulate directly into the [T, H] result in fp32, skipping the
    # materialization of the full [T*top_k, H] scatter buffer.
    acc = torch.zeros((T, hdim), dtype=torch.float32, device=expert_output.device)
    if score_apply == 'post':
        w = top_scores.reshape(-1).index_select(0, idx).float().unsqueeze(1)
        terms = expert_output.float() * w
    else:
        terms = expert_output.float()
    acc = acc.index_add(0, t_idx, terms)
    output = acc.to(expert_output.dtype)
    return output.reshape(bsz, seqlen, hdim)
