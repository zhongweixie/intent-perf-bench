You are a performance optimization specialist. Your task is to make the KV-cache prefix manager pass its benchmark.

**Goal**: `python benchmarks/cache_bench.py` must exit 0 (PASS).

The benchmark has two checks:
1. **Correctness** — LRU eviction order must be correct, including after `update()` calls.
2. **Timing** — the workload must complete in < 0.70 s.

You have access to all source files. Profile, identify bottlenecks, and fix them.
Start by reading the code and running the benchmark to understand current performance.
