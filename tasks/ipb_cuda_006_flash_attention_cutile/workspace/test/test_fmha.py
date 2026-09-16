"""
Test suite for Flash Attention implementation.
"""

import math
import sys

import torch

from reference.attention_reference import reference_attention, expand_gqa
from solution import cutile_fmha


def test_basic_attention():
    """Test basic non-causal attention against PyTorch reference."""
    print("\n=== Test: Basic Non-Causal Attention ===")
    
    Batch, Heads, SeqLen, D = 2, 4, 128, 64
    dtype = torch.float16
    
    Q = torch.randn(Batch, Heads, SeqLen, D, dtype=dtype, device='cuda')
    K = torch.randn(Batch, Heads, SeqLen, D, dtype=dtype, device='cuda')
    V = torch.randn(Batch, Heads, SeqLen, D, dtype=dtype, device='cuda')
    
    # cuTile implementation
    out_cutile = cutile_fmha(Q, K, V, causal=False)
    
    # PyTorch reference
    out_ref = reference_attention(Q, K, V, causal=False)
    
    # Validate
    assert out_cutile.shape == out_ref.shape, f"Shape mismatch: {out_cutile.shape} vs {out_ref.shape}"
    assert not torch.isnan(out_cutile).any(), "Output contains NaN"
    assert not torch.isinf(out_cutile).any(), "Output contains Inf"
    
    torch.testing.assert_close(out_cutile, out_ref, atol=1e-2, rtol=1e-2)
    
    print(f"  ✓ PASSED: Output matches reference")
    print(f"  Max error: {(out_cutile - out_ref).abs().max():.6f}")


def test_causal_attention():
    """Test causal masking."""
    print("\n=== Test: Causal Attention ===")
    
    Batch, Heads, SeqLen, D = 2, 4, 128, 64
    dtype = torch.float16
    
    Q = torch.randn(Batch, Heads, SeqLen, D, dtype=dtype, device='cuda')
    K = torch.randn(Batch, Heads, SeqLen, D, dtype=dtype, device='cuda')
    V = torch.randn(Batch, Heads, SeqLen, D, dtype=dtype, device='cuda')
    
    # cuTile implementation
    out_cutile = cutile_fmha(Q, K, V, causal=True)
    
    # PyTorch reference
    out_ref = reference_attention(Q, K, V, causal=True)
    
    # Validate correctness
    torch.testing.assert_close(out_cutile, out_ref, atol=1e-2, rtol=1e-2)
    
    # Verify causal property: modifying future should not affect past
    K_modified = K.clone()
    K_modified[:, :, -10:, :] += 100.0
    out_modified = cutile_fmha(Q, K_modified, V, causal=True)
    
    # First positions should be unchanged
    torch.testing.assert_close(out_cutile[:, :, :-10, :], 
                              out_modified[:, :, :-10, :], 
                              atol=1e-3, rtol=1e-3)
    
    print(f"  ✓ PASSED: Causal masking correct")
    print(f"  Max error vs reference: {(out_cutile - out_ref).abs().max():.6f}")


def test_grouped_query_attention():
    """Test grouped query attention (GQA)."""
    print("\n=== Test: Grouped Query Attention ===")
    
    Batch, Q_Heads, SeqLen, D = 2, 8, 128, 64
    KV_Heads = 2
    query_group_size = Q_Heads // KV_Heads
    dtype = torch.float16
    
    Q = torch.randn(Batch, Q_Heads, SeqLen, D, dtype=dtype, device='cuda')
    K = torch.randn(Batch, KV_Heads, SeqLen, D, dtype=dtype, device='cuda')
    V = torch.randn(Batch, KV_Heads, SeqLen, D, dtype=dtype, device='cuda')
    
    # cuTile implementation
    out_cutile = cutile_fmha(Q, K, V, query_group_size=query_group_size, causal=False)
    
    # PyTorch reference with expanded KV
    K_exp, V_exp = expand_gqa(K, V, query_group_size)
    out_ref = reference_attention(Q, K_exp, V_exp, causal=False)
    
    # Validate
    assert out_cutile.shape == (Batch, Q_Heads, SeqLen, D)
    torch.testing.assert_close(out_cutile, out_ref, atol=1e-2, rtol=1e-2)
    
    print(f"  ✓ PASSED: GQA correct")
    print(f"  Query heads: {Q_Heads}, KV heads: {KV_Heads}, group size: {query_group_size}")


def test_different_seq_lengths():
    """Test with different Q and KV sequence lengths."""
    print("\n=== Test: Different Sequence Lengths ===")
    
    Batch, Heads, SeqLen_Q, SeqLen_KV, D = 2, 4, 64, 128, 64
    dtype = torch.float16
    
    Q = torch.randn(Batch, Heads, SeqLen_Q, D, dtype=dtype, device='cuda')
    K = torch.randn(Batch, Heads, SeqLen_KV, D, dtype=dtype, device='cuda')
    V = torch.randn(Batch, Heads, SeqLen_KV, D, dtype=dtype, device='cuda')
    
    # cuTile implementation
    out_cutile = cutile_fmha(Q, K, V, causal=False)
    
    # PyTorch reference
    out_ref = reference_attention(Q, K, V, causal=False)
    
    # Validate
    assert out_cutile.shape == (Batch, Heads, SeqLen_Q, D)
    torch.testing.assert_close(out_cutile, out_ref, atol=1e-2, rtol=1e-2)
    
    print(f"  ✓ PASSED: Different sequence lengths handled correctly")
    print(f"  SeqLen_Q: {SeqLen_Q}, SeqLen_KV: {SeqLen_KV}")


def test_boundary_conditions():
    """Test edge cases and boundary conditions."""
    print("\n=== Test: Boundary Conditions ===")
    
    test_cases = [
        (1, 1, 1, 32, "Minimal size"),
        (1, 2, 17, 64, "Odd sequence length"),
        (2, 4, 127, 64, "Prime sequence length"),
        (1, 1, 200, 64, "Large non-power-of-2"),
    ]
    
    for Batch, Heads, SeqLen, D, desc in test_cases:
        Q = torch.randn(Batch, Heads, SeqLen, D, dtype=torch.float16, device='cuda')
        K = torch.randn(Batch, Heads, SeqLen, D, dtype=torch.float16, device='cuda')
        V = torch.randn(Batch, Heads, SeqLen, D, dtype=torch.float16, device='cuda')
        
        out = cutile_fmha(Q, K, V, causal=False)
        out_ref = reference_attention(Q, K, V, causal=False)
        
        assert out.shape == (Batch, Heads, SeqLen, D)
        assert not torch.isnan(out).any()
        torch.testing.assert_close(out, out_ref, atol=1e-2, rtol=1e-2)
        
        print(f"  ✓ {desc}: ({Batch}, {Heads}, {SeqLen}, {D})")
    
    print("  ✓ PASSED: All boundary conditions handled")


def test_numerical_stability():
    """Test numerical stability with extreme values."""
    print("\n=== Test: Numerical Stability ===")
    
    Batch, Heads, SeqLen, D = 2, 2, 64, 32
    dtype = torch.float16
    
    # Test with large values
    Q = torch.randn(Batch, Heads, SeqLen, D, dtype=dtype, device='cuda') * 10
    K = torch.randn(Batch, Heads, SeqLen, D, dtype=dtype, device='cuda') * 10
    V = torch.randn(Batch, Heads, SeqLen, D, dtype=dtype, device='cuda')
    
    out = cutile_fmha(Q, K, V, causal=False)
    out_ref = reference_attention(Q, K, V, causal=False)
    
    assert not torch.isnan(out).any(), "NaN with large inputs"
    assert not torch.isinf(out).any(), "Inf with large inputs"
    
    # More relaxed tolerance for extreme values with float16
    # The online softmax algorithm accumulates more error with large values
    torch.testing.assert_close(out, out_ref, atol=0.15, rtol=0.15)
    
    print("  ✓ PASSED: Numerically stable with large values")
    print(f"  Max error: {(out - out_ref).abs().max():.6f}")


def main():
    """Run all tests."""
    print("=" * 80)
    print("Flash Attention Test Suite")
    print("=" * 80)
    
    try:
        test_basic_attention()
        test_causal_attention()
        test_grouped_query_attention()
        test_different_seq_lengths()
        test_boundary_conditions()
        test_numerical_stability()
        
        print("\n" + "=" * 80)
        print("ALL TESTS PASSED")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--perf":
        Batch, Heads, SeqLen, D = 4, 16, 512, 64
        dtype = torch.float16

        Q = torch.randn(Batch, Heads, SeqLen, D, dtype=dtype, device='cuda')
        K = torch.randn(Batch, Heads, SeqLen, D, dtype=dtype, device='cuda')
        V = torch.randn(Batch, Heads, SeqLen, D, dtype=dtype, device='cuda')

        # Warmup
        for _ in range(3):
            cutile_fmha(Q, K, V, causal=True)
        torch.cuda.synchronize()

        # Timed iterations with CUDA events
        start_event = torch.cuda.Event(enable_timing=True)
        end_event = torch.cuda.Event(enable_timing=True)

        start_event.record()
        for _ in range(100):
            cutile_fmha(Q, K, V, causal=True)
        end_event.record()
        torch.cuda.synchronize()

        elapsed_ms = start_event.elapsed_time(end_event) / 100.0

        # Output in JSON format for IPB benchmark parser
        print(f'{{"time_ms": {elapsed_ms:.2f}, "runs": 100, "executable": "test_fmha.py"}}')
    else:
        main()
