# SPDX-License-Identifier: Apache-2.0
# DeepSpeed Team. Export of upstream local token functions; only import paths adapted.
from __future__ import annotations
import torch
from typing import Literal

class _GatherRows(torch.autograd.Function):
    """out[i] = src[map_idx[i]] if map_idx[i] >= 0 else 0.

    Backward scatters grad rows to their (unique) source rows with a
    non-atomic index_copy_, avoiding slow low-precision atomicAdd.
    """
    @staticmethod
    def forward(ctx, src, map_idx):
        out = torch.index_select(src, 0, map_idx.clamp_min(0))
        out = out * (map_idx >= 0).unsqueeze(1).to(out.dtype)
        ctx.save_for_backward(map_idx)
        ctx.n_src = src.shape[0]
        return out

    @staticmethod
    def backward(ctx, grad_out):
        (map_idx,) = ctx.saved_tensors
        valid = map_idx >= 0
        grad_src = grad_out.new_zeros((ctx.n_src, grad_out.shape[1]))
        grad_src.index_copy_(0, map_idx[valid], grad_out[valid])
        return grad_src, None


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
    if use_cpu:
        tokens_padded = torch.vstack((tokens, tokens.new_zeros((tokens.shape[-1],))))
        tokens_permuted = tokens_padded[permuted_indices, :]
        return (tokens_permuted, permuted_indices, m_sizes, n_tokens)
    tokens_permuted = _GatherRows.apply(tokens, permuted_indices.to(torch.int64))
    return (tokens_permuted, permuted_indices, m_sizes, n_tokens)

def unpermute_by_local_expert(expert_output: torch.Tensor, permuted_indices: torch.Tensor, n_tokens: int) -> torch.Tensor:
    """Reverse permute_by_local_expert: restore original token order and strip padding.

    Args:
        expert_output: [N_padded, H] from expert computation
        permuted_indices: [N_padded] index mapping from permute_by_local_expert
        n_tokens: original token count before alignment padding
    """
    if expert_output.device.type == 'cpu':
        out_unpermuted = expert_output.new_zeros((n_tokens + 1, expert_output.shape[-1]))
        out_unpermuted[permuted_indices, :] = expert_output
        return out_unpermuted[:-1]
    # Build inverse map token -> padded position (every token is covered exactly once).
    perm64 = permuted_indices.to(torch.int64)
    valid = perm64 >= 0
    inv = perm64.new_full((n_tokens,), -1)
    inv[perm64[valid]] = valid.nonzero().squeeze(1)
    return _GatherRows.apply(expert_output, inv)

def combine_from_routed(expert_output: torch.Tensor, top_scores: torch.Tensor, token_indices_sorted: torch.Tensor, top_k: int, score_apply: Literal['pre', 'post'], combine_impl: Literal['weighted_sum', 'legacy_bmm'], shape: tuple[int, int, int]) -> torch.Tensor:
    """Scatter-add expert outputs back to original token positions."""
    bsz, seqlen, hdim = shape
    T = bsz * seqlen
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
