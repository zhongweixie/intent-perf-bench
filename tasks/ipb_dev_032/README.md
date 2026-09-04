# ipb_dev_032: Percentile Redundant Sort

## Overview

Performance benchmark task testing agent ability to diagnose and fix redundant sorting inside a loop.

## Problem Description

The metric collection pipeline has regressed from ~0.028s to ~0.114s (4x slowdown). The bottleneck is in `metric_collector/collector.py` where `compute_percentiles()` calls `sorted()` once per percentile target instead of sorting once before the loop.

## Workspace Structure

```
workspace/
├── metric_collector/
│   ├── __init__.py
│   └── collector.py        # PERFORMANCE BOTTLENECK HERE
├── benchmarks/
│   └── metric_bench.py     # Performance test (threshold: 0.10s)
├── run_pipeline.py         # Interactive pipeline runner
├── generate_data.py        # Test data generation
├── test_metrics.json       # 150k metric samples
└── profiling_data.txt      # cProfile evidence (variant: exact_evidence)
```

## Ground Truth

**Bottleneck**: `compute_percentiles()` sorts inside the per-percentile loop

**Root Cause**:
```python
# SLOW: sorts 150k values 4 times (once per percentile)
for p in percentiles:
    sorted_values = sorted(values)  # O(n log n) × 4
    ...
```

**Solution**: Sort once before loop
```python
# FAST: sort once, reuse sorted list
sorted_values = sorted(values)
n = len(sorted_values)
for p in percentiles:
    index = min(int(n * p / 100), n - 1)
    result[p] = sorted_values[index]
```

## Git History

- Commit 1 (baseline): Single sort outside loop - FAST
- Commit 2 (regression): "refactor: re-sort for each percentile to ensure accuracy" - SLOW
- Commit 3: Add profiling evidence
