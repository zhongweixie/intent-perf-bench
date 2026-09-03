You are a performance optimization specialist. Your task is to make the KV-cache prefix manager pass its benchmark.

**Goal**: `python benchmarks/cache_bench.py` must exit 0 (PASS).

The benchmark has two checks:
1. **Correctness** — LRU eviction order must be correct, including after `update()` calls.
2. **Timing** — the workload must complete in < 0.70 s.

**Analysis context**: Initial profiling suggests the bottleneck might be in the cache lookup or eviction logic. The LRU data structure operations (finding entries, updating access times, or evicting old entries) could be inefficient for the large workload size.

Consider investigating the data structures used for tracking cache entries and whether there are redundant lookups or linear scans that could be optimized.
