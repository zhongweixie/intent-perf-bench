# Exact Variant

Optimize the LayerNorm CUDA kernel in `src/layernorm.cu`. The current implementation processes each row with a single thread using serial loops for mean and variance computation, resulting in poor GPU utilization.

## Current Implementation

- Each thread processes one entire row independently
- Block size is set to 32, leading to low occupancy
- Three serial passes over the feature dimension C:
  1. Sum for mean
  2. Sum of squared differences for variance
  3. Normalize and scale

## Performance Target

The baseline processes N=8192 rows of C=768 features in approximately 0.21 ms. Your optimized version should achieve at least 0.08 ms while maintaining numerical correctness within 1e-4 relative tolerance.

## Constraints

- Do not modify `src/layernorm.h`, `test/test_main.cu`, or `Makefile`
- Preserve the function signature of `layernorm_forward`
- The kernel must produce bit-exact results for mean/rstd outputs
- Final normalized outputs must match within 1e-4 relative error

## Optimization Directions

Consider multiple optimization strategies:

1. **Parallelism**: Currently each thread handles an entire row serially. Can you parallelize within a row?
2. **Block configuration**: The 32-thread block size may not fully utilize SM resources
3. **Memory access**: Are there opportunities for coalescing or reducing redundant loads?
4. **Reduction patterns**: The three serial loops could benefit from efficient parallel reduction
5. **Occupancy**: Can you improve warp utilization or increase blocks per SM?

Analyze the bottleneck using profiling or reasoning about memory bandwidth, compute throughput, and synchronization overhead. Implement your optimization, verify correctness with `make clean && make && ./layernorm_test`, and measure performance with `./layernorm_test --benchmark`.
