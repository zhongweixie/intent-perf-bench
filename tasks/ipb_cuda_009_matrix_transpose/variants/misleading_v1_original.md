# Matrix Transpose Global Memory Coalescing Issue

Our CUDA matrix transpose kernel is experiencing severe performance degradation due to uncoalesced global memory accesses. GPU profiling shows extremely poor memory transaction efficiency, with the memory controller issuing far more transactions than necessary for the amount of data transferred.

## Your Task

Investigate the global memory access patterns in `solution.cu` and improve memory coalescing. The current implementation is causing the GPU to issue excessive memory transactions due to scattered, unaligned memory accesses, severely limiting bandwidth utilization.

## Requirements

- Maintain functional correctness: `make clean && make && ./transpose_test` must pass
- Implement the kernel function `k_transpose` as specified in `include/transpose.h`
- Transpose square matrices of size N×N (N=4096 in benchmark)
- Do not modify the header file

## Context

Matrix transpose is a fundamental operation that transforms matrix A to A^T where A^T[i][j] = A[j][i].

Current profiling results show:
- Global memory transactions: 16x higher than theoretical minimum
- Memory coalescing efficiency: 6.25% (extremely poor)
- Global memory bandwidth: Only 8% of peak (severely underutilized)

This indicates threads are accessing global memory in a highly scattered pattern, causing the hardware to issue many small transactions instead of efficient coalesced 128-byte transactions.

## Files

- `solution.cu` - CUDA kernel implementation (optimize this)
- `include/transpose.h` - kernel signature and constants
- `test/test_main.cu` - correctness and performance tests
- `Makefile` - build configuration

## Hints

Focus on improving the coalescing of global memory accesses. Consider how threads in a warp access memory - can you ensure they read/write consecutive addresses? Think about restructuring the memory access pattern so that adjacent threads access adjacent memory locations in both the read and write phases. Consider using larger data types or vectorized loads to improve transaction efficiency.
