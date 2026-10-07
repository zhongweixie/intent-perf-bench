# Optional implementation space for local token kernels.
# Fused Triton kernels for the local token-movement pipeline.
from __future__ import annotations
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
    def _gather_pad_fwd(x_ptr, perm_ptr, out_ptr, H: tl.constexpr, BLOCK_H: tl.constexpr):
        # out[i] = x[perm[i]] if perm[i] >= 0 else 0
        i = tl.program_id(0)
        hb = tl.program_id(1)
        offs = hb * BLOCK_H + tl.arange(0, BLOCK_H)
        m = offs < H
        p = tl.load(perm_ptr + i).to(tl.int64)
        if p >= 0:
            v = tl.load(x_ptr + p * H + offs, mask=m, other=0.0).to(tl.float32)
        else:
            v = tl.zeros((BLOCK_H,), dtype=tl.float32)
        tl.store(out_ptr + i * H + offs, v, mask=m)

    @triton.jit
    def _gather_pad_bwd(g_ptr, perm_ptr, gx_ptr, H: tl.constexpr, BLOCK_H: tl.constexpr):
        # gx[perm[i]] += g[i] for perm[i] >= 0
        i = tl.program_id(0)
        hb = tl.program_id(1)
        p = tl.load(perm_ptr + i).to(tl.int64)
        if p >= 0:
            offs = hb * BLOCK_H + tl.arange(0, BLOCK_H)
            m = offs < H
            v = tl.load(g_ptr + i * H + offs, mask=m, other=0.0).to(tl.float32)
            tl.atomic_add(gx_ptr + p * H + offs, v, mask=m)

    @triton.jit
    def _scatter_fwd(x_ptr, perm_ptr, out_ptr, H: tl.constexpr, BLOCK_H: tl.constexpr):
        # out[perm[i]] = x[i] for perm[i] >= 0  (out fully covered for valid counts)
        i = tl.program_id(0)
        hb = tl.program_id(1)
        p = tl.load(perm_ptr + i).to(tl.int64)
        if p >= 0:
            offs = hb * BLOCK_H + tl.arange(0, BLOCK_H)
            m = offs < H
            v = tl.load(x_ptr + i * H + offs, mask=m, other=0.0)
            tl.store(out_ptr + p * H + offs, v, mask=m)

    @triton.jit
    def _scatter_bwd_gather(g_ptr, perm_ptr, gx_ptr, H: tl.constexpr, BLOCK_H: tl.constexpr):
        # gx[i] = g[perm[i]] if perm[i] >= 0 else 0
        i = tl.program_id(0)
        hb = tl.program_id(1)
        offs = hb * BLOCK_H + tl.arange(0, BLOCK_H)
        m = offs < H
        p = tl.load(perm_ptr + i).to(tl.int64)
        if p >= 0:
            v = tl.load(g_ptr + p * H + offs, mask=m, other=0.0).to(tl.float32)
        else:
            v = tl.zeros((BLOCK_H,), dtype=tl.float32)
        tl.store(gx_ptr + i * H + offs, v, mask=m)

    @triton.jit
    def _combine_fwd(x_ptr, s_ptr, inv_ptr, out_ptr,
                     K: tl.constexpr, H: tl.constexpr, BLOCK_H: tl.constexpr):
        # out[t] = sum_k s[t,k] * x[inv[t*K+k]]  (fp32 accumulation; inv=-1 -> 0)
        t = tl.program_id(0)
        hb = tl.program_id(1)
        offs = hb * BLOCK_H + tl.arange(0, BLOCK_H)
        m = offs < H
        acc = tl.zeros((BLOCK_H,), dtype=tl.float32)
        for k in range(K):
            idx = tl.load(inv_ptr + t * K + k).to(tl.int64)
            valid = idx >= 0
            idxc = tl.where(valid, idx, 0)
            s = tl.load(s_ptr + t * K + k).to(tl.float32)
            x = tl.load(x_ptr + idxc * H + offs, mask=m & valid, other=0.0)
            acc += s * x.to(tl.float32)
        tl.store(out_ptr + t * H + offs, acc, mask=m)

    @triton.jit
    def _combine_bwd_x(g_ptr, s_ptr, idx_ptr, gx_ptr,
                       K: tl.constexpr, H: tl.constexpr, BLOCK_H: tl.constexpr):
        # gx[i] = g[idx[i]//K] * s_flat[idx[i]]
        i = tl.program_id(0)
        hb = tl.program_id(1)
        offs = hb * BLOCK_H + tl.arange(0, BLOCK_H)
        m = offs < H
        idx = tl.load(idx_ptr + i).to(tl.int64)
        t = idx // K
        s = tl.load(s_ptr + idx).to(tl.float32)
        g = tl.load(g_ptr + t * H + offs, mask=m, other=0.0)
        tl.store(gx_ptr + i * H + offs, g.to(tl.float32) * s, mask=m)

    @triton.jit
    def _combine_bwd_s(g_ptr, x_ptr, inv_ptr, gs_ptr,
                       K: tl.constexpr, H: tl.constexpr, BLOCK_H: tl.constexpr):
        # gs_flat[j] = sum_h g[j//K, h] * x[inv[j], h]  (fp32 accumulation; inv=-1 -> 0)
        j = tl.program_id(0)
        idx = tl.load(inv_ptr + j).to(tl.int64)
        valid = idx >= 0
        idxc = tl.where(valid, idx, 0)
        t = j // K
        acc = tl.zeros((BLOCK_H,), dtype=tl.float32)
        for hb in range(0, H, BLOCK_H):
            offs = hb + tl.arange(0, BLOCK_H)
            m = offs < H
            g = tl.load(g_ptr + t * H + offs, mask=m, other=0.0).to(tl.float32)
            x = tl.load(x_ptr + idxc * H + offs, mask=m & valid, other=0.0).to(tl.float32)
            acc += g * x
        tl.store(gs_ptr + j, tl.sum(acc))


def _block_h(H: int) -> int:
    if H % 2048 == 0:
        return 2048
    if H % 1024 == 0:
        return 1024
    if H % 512 == 0:
        return 512
    return 256


class GatherPad(torch.autograd.Function):
    """out[i] = x[perm[i]] if perm[i] >= 0 else 0 (forward of permute)."""

    @staticmethod
    def forward(ctx, x, perm):
        n_pad, H = perm.shape[0], x.shape[1]
        out = x.new_empty((n_pad, H))
        B = _block_h(H)
        grid = (n_pad, triton.cdiv(H, B))
        _gather_pad_fwd[grid](x, perm, out, H=H, BLOCK_H=B, num_warps=8)
        ctx.save_for_backward(perm)
        ctx.x_shape = x.shape
        ctx.x_dtype = x.dtype
        return out

    @staticmethod
    def backward(ctx, g):
        (perm,) = ctx.saved_tensors
        gx = torch.zeros(ctx.x_shape, dtype=torch.float32, device=g.device)
        B = _block_h(g.shape[1])
        grid = (perm.shape[0], triton.cdiv(g.shape[1], B))
        _gather_pad_bwd[grid](g.contiguous(), perm, gx, H=g.shape[1], BLOCK_H=B, num_warps=8)
        return gx.to(ctx.x_dtype), None


class ScatterRows(torch.autograd.Function):
    """out[perm[i]] = x[i] for perm[i] >= 0 (forward of unpermute; valid counts cover all rows)."""

    @staticmethod
    def forward(ctx, x, perm, n):
        H = x.shape[1]
        out = x.new_empty((n, H))
        B = _block_h(H)
        grid = (perm.shape[0], triton.cdiv(H, B))
        _scatter_fwd[grid](x, perm, out, H=H, BLOCK_H=B, num_warps=8)
        ctx.save_for_backward(perm)
        return out

    @staticmethod
    def backward(ctx, g):
        (perm,) = ctx.saved_tensors
        n_pad = perm.shape[0]
        H = g.shape[1]
        gx = g.new_empty((n_pad, H))
        B = _block_h(H)
        grid = (n_pad, triton.cdiv(H, B))
        _scatter_bwd_gather[grid](g.contiguous(), perm, gx, H=H, BLOCK_H=B, num_warps=8)
        return gx, None, None


class CombineFused(torch.autograd.Function):
    """out[t] = sum_k s[t,k] * x[idx[t*K+k]] with fp32 accumulation."""

    @staticmethod
    def forward(ctx, x, s, idx, T, K):
        N, H = x.shape
        TK = T * K
        inv = torch.full((TK,), -1, dtype=torch.int64, device=x.device)
        inv[idx.long()] = torch.arange(N, dtype=torch.int64, device=x.device)
        out = torch.empty((T, H), dtype=x.dtype, device=x.device)
        B = _block_h(H)
        grid = (T, triton.cdiv(H, B))
        _combine_fwd[grid](x, s, inv, out, K=K, H=H, BLOCK_H=B, num_warps=8)
        ctx.save_for_backward(x, s, idx, inv)
        ctx.K = K
        ctx.TK = TK
        return out

    @staticmethod
    def backward(ctx, g):
        x, s, idx, inv = ctx.saved_tensors
        K = ctx.K
        T = ctx.TK // K
        N, H = x.shape
        g = g.contiguous()
        B = _block_h(H)
        grid = (N, triton.cdiv(H, B))
        gx = torch.empty((N, H), dtype=x.dtype, device=x.device)
        _combine_bwd_x[grid](g, s, idx, gx, K=K, H=H, BLOCK_H=B, num_warps=8)
        gs = torch.empty((T * K,), dtype=s.dtype, device=s.device)
        _combine_bwd_s[(T * K,)](g, x, inv, gs, K=K, H=H, BLOCK_H=min(B, 512), num_warps=4)
        return gx, gs.view(s.shape), None, None, None


def triton_ready(x, *others):
    if not _TRITON_AVAILABLE or x.device.type != 'cuda':
        return False
    for t in (x,) + others:
        if t.stride(-1) != 1:
            return False
    return True
