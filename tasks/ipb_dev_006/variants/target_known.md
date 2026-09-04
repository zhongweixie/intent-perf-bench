# Task: Fix Log Pipeline Performance Regression

The log processing pipeline has become slow. The issue is in the `log_pipeline/enricher.py` module. Please investigate and fix it.

**Available evidence:**
- `profiling_data.txt` — stage-by-stage timing breakdown
- `git.log` — recent commit history
- `benchmarks/log_bench.py` — performance acceptance test

**Requirements:**
- Preserve pipeline output correctness
- Fix the performance issue in the specified module
- Your fix should pass: `python3 benchmarks/log_bench.py`
