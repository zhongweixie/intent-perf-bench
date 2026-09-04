Optimize the CUDA kernel for computing L2 norm of a vector.

The current implementation in `solve.cu` performs hierarchical reduction using shared memory, but has performance issues that slow it down by approximately 4-7x.

Your task:
1. Analyze the `k_l2Norm` kernel in `solve.cu`
2. Identify the performance bottleneck
3. Optimize the kernel to achieve 4-7x speedup
4. Ensure correctness is maintained (run `./l2norm_benchmark --verify`)

Key files:
- `solve.cu`: Contains the kernel to optimize
- `main.cu`: Test harness with verification and benchmarking
- `include/l2_norm.h`: Kernel interface

Algorithm overview:
- Each thread loads one element from global memory into shared memory
- Threads perform parallel reduction within the block
- Thread 0 writes the block's result to global memory

Build and test:
```bash
make
./l2norm_benchmark --verify
./l2norm_benchmark --benchmark
```

Focus on synchronization patterns and reduction efficiency.
