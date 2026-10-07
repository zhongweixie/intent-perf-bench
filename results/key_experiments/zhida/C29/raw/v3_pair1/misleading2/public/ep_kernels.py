# Copyright (c) DeepSpeed Team.
# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
# SPDX-License-Identifier: Apache-2.0 AND BSD-3-Clause
#
# Portions of this file are derived from TorchTitan.
# See THIRD_PARTY_NOTICES.md for the BSD-3-Clause notice.

# DeepSpeed Team
"""
Token reordering and permutation utilities for expert parallelism.

Ported from TorchTitan's Triton kernels and alignment
utilities with adaptations for DeepSpeed:
  - Triton import guarded with try/except; pure-PyTorch fallback provided
  - Alignment config exposed as TOKEN_GROUP_ALIGN_SIZE_M

This module is self-contained: no imports from deepspeed.module_inject
or deepspeed.runtime.
"""

import logging
from typing import Callable

import torch

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Try to import Triton; fall back gracefully
# ---------------------------------------------------------------------------

_TRITON_AVAILABLE = False
try:
    import triton
    import triton.language as tl

    _TRITON_AVAILABLE = True
except ImportError:
    logger.info("Triton not available; using pure-PyTorch CPU fallback for "
                "permutation index generation.")

# ---------------------------------------------------------------------------
# Alignment constant
# ---------------------------------------------------------------------------

TOKEN_GROUP_ALIGN_SIZE_M = 8
"""Alignment granularity for token groups in grouped GEMM.

 - bf16: 8  (16 bytes / 2 bytes per elem)
 - fp8:  16 (16 bytes / 1 byte per elem)
 - mxfp8: 32 (scaling block size)
"""

# ---------------------------------------------------------------------------
# Utility: round up
# ---------------------------------------------------------------------------


def _round_up(x: int, y: int) -> int:
    """Round *x* up to the nearest multiple of *y*."""
    return ((x + y - 1) // y) * y


# ===================================================================
# Triton kernel for filling permutation indices
# ===================================================================

if _TRITON_AVAILABLE:

    @triton.jit
    def _fill_indices_kernel(
        tokens_per_expert_group_ptr,
        start_index_values_ptr,
        write_offsets_ptr,
        output_ptr,
        experts_per_rank: tl.constexpr,
        num_ranks: tl.constexpr,
        BLOCK_SIZE: tl.constexpr,
    ):
        pid = tl.program_id(axis=0)
        num_programs = tl.num_programs(axis=0)

        for expert_id in range(pid, experts_per_rank, num_programs):
            write_offset = tl.load(write_offsets_ptr + expert_id)

            for r in range(num_ranks):
                i = r * experts_per_rank + expert_id
                start_index = tl.load(start_index_values_ptr + i)
                length = tl.load(tokens_per_expert_group_ptr + i)

                offsets = tl.arange(0, BLOCK_SIZE)
                for chunk_start in range(0, length, BLOCK_SIZE):
                    chunk_offsets = chunk_start + offsets
                    mask = chunk_offsets < length
                    values = start_index + chunk_offsets
                    dest_indices = write_offset + chunk_offsets
                    tl.store(output_ptr + dest_indices, values, mask=mask)

                write_offset += length

    @triton.jit
    def _permute_meta_kernel(
        counts_ptr,
        start_index_values_ptr,
        write_offsets_ptr,
        m_sizes_ptr,
        m_offsets_ptr,
        num_ranks: tl.constexpr,
        experts_per_rank: tl.constexpr,
        alignment: tl.constexpr,
        BLOCK_FLAT: tl.constexpr,
        BLOCK_R: tl.constexpr,
        BLOCK_E: tl.constexpr,
    ):
        """Single-program kernel producing all index-generation metadata.

        Replaces the chain of small torch ops (cumsum, sum, clamp, align,
        cumsum) with one launch.
        """
        offs = tl.arange(0, BLOCK_FLAT)
        flat_mask = offs < num_ranks * experts_per_rank
        counts = tl.load(counts_ptr + offs, mask=flat_mask, other=0).to(tl.int32)

        # Exclusive prefix sum -> start index for each (rank, expert) group
        cum = tl.cumsum(counts, 0)
        tl.store(start_index_values_ptr + offs, cum - counts, mask=flat_mask)

        # Per-expert totals across ranks (source-major [num_ranks, experts])
        r_offs = tl.arange(0, BLOCK_R)[:, None]
        e_offs = tl.arange(0, BLOCK_E)[None, :]
        mask2 = (r_offs < num_ranks) & (e_offs < experts_per_rank)
        c2 = tl.load(counts_ptr + r_offs * experts_per_rank + e_offs,
                     mask=mask2, other=0).to(tl.int32)
        total = tl.sum(c2, 0)
        total = tl.maximum(total, alignment)
        m_sizes = (total + alignment - 1) // alignment * alignment
        m_off = tl.cumsum(m_sizes, 0)

        e1 = tl.arange(0, BLOCK_E)
        e_mask = e1 < experts_per_rank
        tl.store(m_sizes_ptr + e1, m_sizes, mask=e_mask)
        tl.store(m_offsets_ptr + e1, m_off, mask=e_mask)
        tl.store(write_offsets_ptr + e1, m_off - m_sizes, mask=e_mask)

    @triton.jit
    def _row_gather_kernel(
        src_ptr,
        idx_ptr,
        out_ptr,
        H,
        BLOCK_H: tl.constexpr,
    ):
        """out[j, :] = src[idx[j], :] when idx[j] >= 0 else 0."""
        pid = tl.program_id(axis=0)
        idx = tl.load(idx_ptr + pid).to(tl.int64)
        h_offs = tl.arange(0, BLOCK_H)
        src_row = src_ptr + idx * H
        out_row = out_ptr + pid.to(tl.int64) * H
        for h0 in range(0, H, BLOCK_H):
            mask = (h0 + h_offs) < H
            if idx >= 0:
                vals = tl.load(src_row + h0 + h_offs, mask=mask)
            else:
                vals = tl.zeros((BLOCK_H,), dtype=tl.float32).to(out_ptr.dtype.element_ty)
            tl.store(out_row + h0 + h_offs, vals, mask=mask)

    @triton.jit
    def _row_scatter_kernel(
        src_ptr,
        idx_ptr,
        out_ptr,
        H,
        BLOCK_H: tl.constexpr,
    ):
        """out[idx[j], :] = src[j, :] when idx[j] >= 0 (idx unique)."""
        pid = tl.program_id(axis=0)
        idx = tl.load(idx_ptr + pid).to(tl.int64)
        if idx >= 0:
            h_offs = tl.arange(0, BLOCK_H)
            src_row = src_ptr + pid.to(tl.int64) * H
            out_row = out_ptr + idx * H
            for h0 in range(0, H, BLOCK_H):
                mask = (h0 + h_offs) < H
                vals = tl.load(src_row + h0 + h_offs, mask=mask)
                tl.store(out_row + h0 + h_offs, vals, mask=mask)


def _next_pow2(x: int) -> int:
    return max(1, 1 << (int(x) - 1).bit_length())


def row_gather(src: torch.Tensor, idx: torch.Tensor, out: torch.Tensor) -> None:
    """Launch the zero-fill row gather used by permute / unpermute-backward."""
    n_idx, H = out.shape
    if n_idx == 0:
        return
    BLOCK_H = min(_next_pow2(H), 1024)
    _row_gather_kernel[(n_idx,)](src, idx, out, H, BLOCK_H=BLOCK_H,
                                 num_warps=4 if BLOCK_H >= 512 else 2)


def row_scatter(src: torch.Tensor, idx: torch.Tensor, out: torch.Tensor) -> None:
    """Launch the unique-index row scatter used by unpermute / permute-backward."""
    n_idx, H = src.shape
    if n_idx == 0:
        return
    BLOCK_H = min(_next_pow2(H), 1024)
    _row_scatter_kernel[(n_idx,)](src, idx, out, H, BLOCK_H=BLOCK_H,
                                  num_warps=4 if BLOCK_H >= 512 else 2)


def triton_row_ops_available() -> bool:
    return _TRITON_AVAILABLE


# ===================================================================
# Triton wrapper
# ===================================================================


def fill_indices_wrapper(
    tokens_per_expert_group: torch.Tensor,
    start_index_values: torch.Tensor,
    write_offsets: torch.Tensor,
    experts_per_rank: int,
    num_ranks: int,
    max_len: int,
    block_size: int = 128,
    max_blocks: int = 1024,
) -> torch.Tensor:
    """Launch the Triton kernel to fill permutation indices.

    Falls back to :func:`fill_indices_cpu` when Triton is unavailable.
    """
    if not _TRITON_AVAILABLE:
        return fill_indices_cpu(
            tokens_per_expert_group,
            start_index_values,
            write_offsets,
            experts_per_rank,
            num_ranks,
            max_len,
        )

    permuted_indices = torch.full((max_len, ), -1, dtype=torch.int32, device=tokens_per_expert_group.device)

    num_blocks = min(experts_per_rank, max_blocks)
    grid = (num_blocks, )

    _fill_indices_kernel[grid](
        tokens_per_expert_group,
        start_index_values,
        write_offsets,
        permuted_indices,
        experts_per_rank,
        num_ranks,
        BLOCK_SIZE=block_size,
    )
    return permuted_indices


# ===================================================================
# CPU reference implementation (always available)
# ===================================================================


def fill_indices_cpu(
    tokens_per_expert_group: torch.Tensor,
    start_index_values: torch.Tensor,
    write_offsets: torch.Tensor,
    experts_per_rank: int,
    num_ranks: int,
    max_len: int,
) -> torch.Tensor:
    """Pure-PyTorch CPU reference for filling permutation indices."""
    permuted_indices = torch.full(
        (max_len, ),
        -1,
        dtype=torch.int32,
    )
    for e in range(experts_per_rank):
        write_start = write_offsets[e].item()
        for r in range(num_ranks):
            i = r * experts_per_rank + e
            start_index = start_index_values[i].item()
            length = tokens_per_expert_group[i].item()
            if length > 0:
                end_idx = min(write_start + length, max_len)
                permuted_indices[write_start:end_idx] = torch.arange(
                    start_index,
                    start_index + (end_idx - write_start),
                    dtype=torch.int32,
                )
            write_start += length
    return permuted_indices


# ===================================================================
# generate_permute_indices
# ===================================================================


def _generate_meta_torch(tokens_per_expert_group, experts_per_rank, num_ranks):
    """Original small-torch-op metadata chain (fallback path)."""
    start_index_values = (torch.cumsum(tokens_per_expert_group, 0) - tokens_per_expert_group)
    total_tokens_per_expert = tokens_per_expert_group.view(num_ranks, -1).sum(0)
    return start_index_values, total_tokens_per_expert


def generate_permute_indices(
    tokens_per_expert_group: torch.Tensor,
    experts_per_rank: int,
    num_ranks: int,
    max_len: int,
    alignment: int,
    use_cpu: bool = False,
) -> tuple:
    """Prepare permutation indices and aligned token counts per expert.

    Args:
        tokens_per_expert_group: Token counts for each expert from all ranks,
            shape ``(num_ranks * experts_per_rank,)``.
        experts_per_rank: Number of experts per rank.
        num_ranks: Number of ranks.
        max_len: Maximum length of the output index vector.
        alignment: Alignment for ``m_sizes`` and padding minimum.
        use_cpu: Whether to force the CPU implementation.

    Returns:
        Tuple of:
            - permuted_indices: Index mapping from original to expert-grouped order.
            - m_sizes: Aligned token counts per expert.
            - m_offsets: Cumulative sum of m_sizes.
    """
    device = tokens_per_expert_group.device
    n_flat = num_ranks * experts_per_rank

    if use_cpu or not _TRITON_AVAILABLE or n_flat > 4096 or experts_per_rank > 1024:
        # Original torch / CPU fallback path.
        start_index_values, total_tokens_per_expert = _generate_meta_torch(
            tokens_per_expert_group, experts_per_rank, num_ranks)

        # Pad empty experts to alignment minimum
        total_tokens_per_expert = torch.clamp_min(total_tokens_per_expert, alignment)

        # Align chunk sizes (ceiling division * alignment)
        m_sizes = ((total_tokens_per_expert + alignment - 1) // alignment * alignment).to(torch.int32)

        # Write offsets per local expert
        m_offsets = torch.cumsum(m_sizes, 0)
        write_offsets = m_offsets - m_sizes

        if use_cpu:
            permuted_indices = fill_indices_cpu(
                tokens_per_expert_group,
                start_index_values,
                write_offsets,
                experts_per_rank,
                num_ranks,
                max_len,
            )
        else:
            permuted_indices = fill_indices_wrapper(
                tokens_per_expert_group,
                start_index_values,
                write_offsets,
                experts_per_rank,
                num_ranks,
                max_len,
            )
        return permuted_indices, m_sizes, m_offsets.to(torch.int32)

    # Fused single-launch metadata path.
    counts = tokens_per_expert_group
    if not counts.is_contiguous():
        counts = counts.contiguous()
    start_index_values = torch.empty(n_flat, dtype=torch.int32, device=device)
    m_sizes = torch.empty(experts_per_rank, dtype=torch.int32, device=device)
    m_offsets = torch.empty(experts_per_rank, dtype=torch.int32, device=device)
    write_offsets = torch.empty(experts_per_rank, dtype=torch.int32, device=device)

    BLOCK_FLAT = _next_pow2(n_flat)
    BLOCK_R = _next_pow2(num_ranks)
    BLOCK_E = _next_pow2(experts_per_rank)
    _permute_meta_kernel[(1,)](
        counts,
        start_index_values,
        write_offsets,
        m_sizes,
        m_offsets,
        num_ranks,
        experts_per_rank,
        alignment,
        BLOCK_FLAT=BLOCK_FLAT,
        BLOCK_R=BLOCK_R,
        BLOCK_E=BLOCK_E,
    )

    permuted_indices = torch.full((max_len, ), -1, dtype=torch.int32, device=device)
    num_blocks = min(experts_per_rank, 1024)
    _fill_indices_kernel[(num_blocks,)](
        counts,
        start_index_values,
        write_offsets,
        permuted_indices,
        experts_per_rank,
        num_ranks,
        BLOCK_SIZE=128,
    )

    return permuted_indices, m_sizes, m_offsets


# ===================================================================
# _permute / _unpermute / indices_padding_wrapper
# ===================================================================


def _permute(
    x: torch.Tensor,
    num_tokens_per_expert: torch.Tensor,
    ep_degree: int,
    num_local_experts: int,
) -> tuple:
    """Permute tokens into expert-grouped order with alignment padding.

    Returns:
        Tuple of (input_shape, permuted_x, permuted_indices, aligned_counts).
    """
    global TOKEN_GROUP_ALIGN_SIZE_M
    x_padded_per_expert = x.shape[0] + num_local_experts * TOKEN_GROUP_ALIGN_SIZE_M
    padded_max_len = _round_up(x_padded_per_expert, TOKEN_GROUP_ALIGN_SIZE_M)

    with torch.no_grad():
        permuted_indices, num_tokens_per_expert, _offsets = generate_permute_indices(
            num_tokens_per_expert,
            num_local_experts,
            ep_degree,
            padded_max_len,
            TOKEN_GROUP_ALIGN_SIZE_M,
        )

    # Append a single zero-row for safe indexing of padding slots
    x = torch.vstack((x, x.new_zeros((x.shape[-1]))))
    input_shape = x.shape
    x = x[permuted_indices, :]

    return input_shape, x, permuted_indices, num_tokens_per_expert


def _unpermute(
    out: torch.Tensor,
    input_shape: torch.Size,
    permuted_indices: torch.Tensor,
) -> torch.Tensor:
    """Reverse the permutation produced by :func:`_permute`."""
    out_unpermuted = out.new_empty(input_shape)
    out_unpermuted[permuted_indices, :] = out
    # Strip the extra zero-row appended during _permute
    out = out_unpermuted[:-1]
    return out
