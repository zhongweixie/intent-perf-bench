# ipb_dev_015: Log Aggregation Performance Regression

## Overview

Performance benchmark task testing agent ability to diagnose and fix a DataFrame aggregation bottleneck in a log processing pipeline.

## Problem Description

The log aggregation pipeline has regressed from ~0.3s to ~3.6s (12x slowdown). The bottleneck is in `log_aggregator/aggregator.py` where iterative `pd.concat()` in a loop creates quadratic copying overhead.

## Workspace Structure

```
workspace/
├── log_aggregator/
│   ├── __init__.py
│   ├── loader.py          # Log data generation
│   ├── aggregator.py      # PERFORMANCE BOTTLENECK HERE
│   └── reporter.py        # Summary statistics
├── benchmarks/
│   └── log_agg_bench.py   # Performance test (threshold: 0.40s)
├── run_pipeline.py        # Interactive pipeline runner
└── profiling_data.txt     # cProfile evidence (variant: exact_evidence)
```

## Test Variants

### 1. exact_evidence
- Provides profiling data showing the bottleneck
- System prompt explicitly mentions available evidence files
- Tests agent's ability to interpret profiling data and apply fix

### 2. fuzzy_context
- Minimal context: "pipeline has become noticeably slower"
- No profiling data provided upfront
- Tests agent's investigation and diagnosis capabilities

## Ground Truth

**Bottleneck**: `aggregate_by_window()` uses iterative `pd.concat([result, stats])` 

**Root Cause**: Each concat creates a full copy of accumulated result, causing O(n²) behavior with 500 time windows

**Solution**: Batch approach
```python
# Collect all stats in list
stats_list = []
for window_time, group in logs.groupby('window'):
    stats_list.append({...})

# Single concat at end
return pd.DataFrame(stats_list)
```

**Expected Outcome**: ~10x speedup (3.6s → 0.3s), benchmark passes

## Evaluation Criteria

1. **Performance**: `python3 benchmarks/log_agg_bench.py` exits 0 (best time ≤ 0.40s)
2. **Correctness**: Aggregation results unchanged (same window counts, statistics)
3. **Code Quality**: Fix targets root cause, not symptoms

## Git History

- Commit 1 (baseline): List accumulation approach - FAST
- Commit 2 (regression): "refactor: use iterative concat for better memory control" - SLOW

The regression commit message is intentionally misleading (claims "better memory control").

## Running Tests

```bash
cd tasks/ipb_dev_015/workspace

# Interactive pipeline with timing breakdown
python3 run_pipeline.py

# Performance benchmark
python3 benchmarks/log_agg_bench.py
```

## Success Indicators

Agent should:
1. Identify `aggregator.py` as bottleneck (via profiling, git history, or code inspection)
2. Recognize iterative concat anti-pattern
3. Refactor to batch collection + single concat
4. Validate with benchmark showing best_time ≤ 0.40s
5. Verify correctness (aggregation results unchanged)

## Notes

- Profiling data intentionally shows high `pandas.concat` cumulative time
- Git log provides narrative clue: regression introduced in recent "refactor" commit
- The misleading commit message tests whether agent validates claims vs measures actual behavior
