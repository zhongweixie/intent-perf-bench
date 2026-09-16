"""
Reference implementation of attention patterns for validation.
This file provides PyTorch-based reference implementations.
"""
import torch
import math


def reference_attention(Q: torch.Tensor, K: torch.Tensor, V: torch.Tensor,
                       qk_scale: float | None = None,
                       causal: bool = False) -> torch.Tensor:
    """
    Reference multi-head attention using PyTorch.
    
    Args:
        Q: Query tensor (Batch, Heads, SeqLen_Q, D_k)
        K: Key tensor (Batch, Heads, SeqLen_KV, D_k)
        V: Value tensor (Batch, Heads, SeqLen_KV, D_v)
        qk_scale: Scaling factor (default: 1/sqrt(D_k))
        causal: Apply causal masking
    
    Returns:
        Output tensor (Batch, Heads, SeqLen_Q, D_v)
    """
    if qk_scale is None:
        qk_scale = 1.0 / math.sqrt(Q.shape[-1])
    
    # Compute attention scores
    attn = torch.matmul(Q, K.transpose(-2, -1)) * qk_scale
    
    # Apply causal mask if needed
    if causal:
        seq_len_q = Q.shape[2]
        seq_len_k = K.shape[2]
        mask = torch.triu(torch.ones(seq_len_q, seq_len_k, device=Q.device), 
                         diagonal=1).bool()
        attn = attn.masked_fill(mask, float('-inf'))
    
    # Softmax and weighted sum
    attn_weights = torch.softmax(attn, dim=-1)
    output = torch.matmul(attn_weights, V)
    
    return output


def expand_gqa(K: torch.Tensor, V: torch.Tensor, 
               query_group_size: int) -> tuple[torch.Tensor, torch.Tensor]:
    """
    Expand KV heads for grouped query attention validation.
    
    Args:
        K: Key tensor (Batch, KV_Heads, SeqLen, D)
        V: Value tensor (Batch, KV_Heads, SeqLen, D)
        query_group_size: Number of query heads per KV head
    
    Returns:
        Expanded K and V tensors
    """
    if query_group_size == 1:
        return K, V
    
    # Repeat each KV head query_group_size times
    K_expanded = K.repeat_interleave(query_group_size, dim=1)
    V_expanded = V.repeat_interleave(query_group_size, dim=1)
    
    return K_expanded, V_expanded