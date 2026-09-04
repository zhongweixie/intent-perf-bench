# Flash Attention Memory Usage Issue

Our multi-head attention implementation is consuming excessive GPU memory, causing out-of-memory errors when processing long sequences in production. The memory footprint appears to grow quadratically with sequence length, which is unsustainable.

## Your Task

Investigate the memory usage in `solution.py` and reduce the memory footprint to handle sequences up to 4096 tokens without OOM errors on our target GPUs (16GB VRAM).

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

Current memory usage pattern:
- Seq len 512: ~2GB
- Seq len 1024: ~8GB
- Seq len 2048: ~32GB (OOM on 16GB cards!)

This quadratic growth suggests we're storing large intermediate matrices unnecessarily.

## Files

- `solution.py` - the attention implementation (optimize this)
- `test/test_fmha.py` - correctness and performance tests
- `reference/attention_reference.py` - reference implementation for correctness checking

## Hints

Look for opportunities to avoid materializing large intermediate tensors. Consider streaming computation patterns that process data in chunks rather than all at once. Some advanced attention algorithms can compute the same result without ever storing the full N×N attention matrix.
