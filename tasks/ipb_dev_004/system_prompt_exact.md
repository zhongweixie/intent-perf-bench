# Performance Issue Investigation (ipb_dev_004 - exact variant)

Your task is to investigate and fix a performance regression in the analytics pipeline.

## Evidence Available

1. **Benchmark Results** (`benchmark_output.txt`):
   - Current performance: ~0.86s (FAIL, threshold: 0.5s)
   - Stage 3 (Calculating metrics) takes 68-81% of total time
   - Stage 1 (Loading data) takes ~0.16s (expected I/O time)

2. **Profiler Output** (`profiler_output.txt`):
   - Shows detailed timing breakdown by function
   - Identifies bottleneck functions

3. **Git History** (`git.log`):
   - Recent commits and changes
   - Can use `git show <commit>` to see specific changes

## Your Goal

Fix the performance regression so the benchmark passes (best time <= 0.5s).

## Available Commands

- `python3 benchmarks/analytics_bench.py` - Run the benchmark
- `git log` / `git show <commit>` - Examine code history
- `git diff <commit1> <commit2>` - Compare versions
- Edit files to implement fixes

## Important Notes

- Focus on Stage 3 (Calculating metrics) - it's the clear bottleneck
- Stage 1 I/O time (~0.16s) is expected and not the problem
- The baseline performance should be around 0.17-0.18s total time
- Use profiler and git history to understand what changed
