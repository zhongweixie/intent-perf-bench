# Exact Variant

Optimize the CUDA NTT butterfly implementation in `solve.cu`. Preserve the exact transform and correctness behavior while reducing the benchmark runtime. Investigate the full pipeline, including stage launches, twiddle-factor generation, global-memory traffic, synchronization, and occupancy. Do not modify `solve.h`, `main.cu`, or `Makefile`.
