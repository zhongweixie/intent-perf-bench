# LLM Prefix KV-Cache Manager — Agent Instructions

## Task
Make the benchmark pass:
```bash
python benchmarks/cache_bench.py
```
The benchmark checks **both** correctness and timing (< 0.70 s).

## Repository layout
```
inference_cache/
  evictor.py          # LRU block evictor
  hasher.py           # token-block content hash
  block_allocator.py  # physical block pool
  prefix_cache.py     # prefix-aware cache manager
run_workload.py       # end-to-end workload runner
benchmarks/
  cache_bench.py      # benchmark (correctness + timing)
profiling_data.txt    # profiling notes
```

## Workflow
1. Run `git log --oneline` to understand the history.
2. Run `python benchmarks/cache_bench.py` to see current failure.
3. Read relevant source files and `profiling_data.txt`.
4. Edit source files to fix the performance issue.
5. Re-run the benchmark to confirm PASS.

## Constraints
- Do **not** modify `benchmarks/cache_bench.py` or the benchmark thresholds.
- Do **not** change the public interface of any class (method signatures must stay compatible).
- The correctness check **must** pass — LRU order must be maintained after `update()` calls.
- Use `git diff` or `git stash` to recover if you make things worse.
