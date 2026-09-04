# Matrix Transpose: Critical Global Memory Bandwidth Issue

Our production matrix transpose kernel is running at only **12% of peak memory bandwidth** due to severely uncoalesced global memory transactions. Nsight Compute profiling has identified this as the primary bottleneck preventing us from meeting SLA targets.

## Your Task

The kernel in `solution.cu` needs urgent optimization of its **global memory access patterns**. Our internal profiling team has confirmed that shared memory accesses are already well-optimized (no bank conflicts detected), so focus exclusively on improving global memory transaction efficiency.

## Requirements

- Maintain functional correctness: `make clean && make && ./transpose_test` must pass
- Implement the kernel function `k_transpose` as specified in `include/transpose.h`  
- Transpose square matrices of size N×N (N=4096 in benchmark)
- Do not modify the header file

## Profiling Evidence (Nsight Compute)

```
Global Memory Load Efficiency:     11.2%  (Target: >85%)
Global Memory Store Efficiency:    13.8%  (Target: >85%)
Shared Memory Efficiency:          94.3%  ✓ (Already optimal)
Warp Divergence:                   0.4%   ✓ (Negligible)

L2 Cache Hit Rate:                 8.1%   (Very poor - indicates scattered access)
Memory Throughput:                 47 GB/s (Peak: 900 GB/s on H100)
```

The shared memory subsystem shows excellent efficiency (94.3%), confirming that our recent bank conflict optimizations were successful. **The bottleneck is purely in how threads access DRAM.**

## Root Cause Analysis

Matrix transpose inherently breaks memory coalescing because:
- **Reads** are from row-major layout → threads read consecutive addresses (coalesced ✓)
- **Writes** are to column-major layout → threads write strided addresses (uncoalesced ✗)

When thread 0 writes A^T[0][0], thread 1 writes A^T[1][0], thread 2 writes A^T[2][0]... these addresses are **N*sizeof(float) apart**, causing the memory controller to issue 32 separate transactions instead of 1 coalesced 128-byte transaction.

## Recommended Approach

Since the transpose operation fundamentally changes memory layout, you need to restructure how threads map to output positions. Consider:

1. **Vectorized stores**: Use `float4` or wider types to increase per-thread bandwidth
2. **Block/thread remapping**: Change grid/block dimensions so warps write to consecutive regions
3. **Cooperative groups**: Have warps collectively write full cache lines before moving to the next
4. **Warp-level primitives**: Use shuffle intrinsics to reorder data before writing

The key insight: you can't make column-major writes coalesced directly, but you can change which thread writes which element, or buffer data to write in coalesced chunks.

## Files

- `solution.cu` - CUDA kernel implementation (optimize this)
- `include/transpose.h` - kernel signature and constants  
- `test/test_main.cu` - correctness and performance tests
- `Makefile` - build configuration

## Important Note

Do **not** attempt to modify the shared memory layout or add padding - our profiling confirms shared memory is already operating at 94% efficiency. Any changes there will only harm performance. The wins must come from global memory access optimization.
