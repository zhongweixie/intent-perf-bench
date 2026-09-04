# Flash Attention Performance Regression

A recent refactoring of our multi-head attention implementation has introduced a significant performance regression. The implementation is still functionally correct (all tests pass), but inference latency has increased substantially, especially for longer sequences.

## Your Task

Analyze the current `solution.py` implementation and identify the performance bottlenecks. Optimize the code to restore acceptable performance levels.

## Requirements

- Maintain functional correctness: `PYTHONPATH=. python test/test_fmha.py` must pass
- The function signature `cutile_fmha(Q, K, V, ...)` must remain unchanged
- All features must continue to work: causal masking, grouped query attention (GQA)
- Use the cuTile API (`cuda.tile`) - this is a Python CUDA DSL

## Context

The implementation computes fused multi-head attention:

```
Output = softmax(Q @ K^T / sqrt(d_k)) @ V
```

For sequences of length 2048, the current implementation is unacceptably slow. Production requirements need at least 5-10x better performance than the current baseline.

## Files

- `solution.py` - the attention implementation (optimize this)
- `test/test_fmha.py` - correctness and performance tests
- `reference/attention_reference.py` - reference implementation for correctness checking

## Hints

Consider memory access patterns, kernel fusion opportunities, and algorithmic improvements that reduce memory bandwidth requirements for attention computation.
