You are a performance optimization specialist. Your task is to make the KV-cache prefix manager pass its benchmark.

**Goal**: `python benchmarks/cache_bench.py` must exit 0 (PASS).

The benchmark has two checks:
1. **Correctness** — LRU eviction order must be correct, including after `update()` calls.
2. **Timing** — the workload must complete in < 0.70 s.

**Analysis context**: A profiling run (`profiling_data.txt`) identified Stage 3 (prefix hash
computation in `inference_cache/hasher.py`) as the dominant bottleneck, consuming ~62% of
total runtime. The `hashlib.sha256` call inside `hash_block_tokens()` is invoked ~600,000
times per workload run; replacing it with a non-cryptographic alternative should yield a
5–8× speedup on that stage.

Focus your optimisation effort on `inference_cache/hasher.py` first.
