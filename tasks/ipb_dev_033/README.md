# ipb_dev_033: Top-K Full Sort Anti-pattern

## Overview

Performance benchmark task testing agent ability to choose the right algorithm for top-k selection.

## Problem Description

The sorting pipeline has regressed from ~0.03s to ~0.13s (4.5x slowdown). The bottleneck is in `sorter/sorter.py` where `find_top_k()` uses `sorted()` + slice to find the top 10 records out of 500k, when `heapq.nlargest()` provides O(n log k) instead of O(n log n).

## Workspace Structure

```
workspace/
├── sorter/
│   ├── __init__.py
│   └── sorter.py           # PERFORMANCE BOTTLENECK HERE
├── benchmarks/
│   └── sort_bench.py       # Performance test (threshold: 0.08s)
├── run_pipeline.py         # Interactive pipeline runner
├── generate_data.py        # Test data generation
├── test_records.json       # 500k records
└── profiling_data.txt      # cProfile evidence (variant: exact_evidence)
```

## Ground Truth

**Bottleneck**: `find_top_k()` sorts all 500k records to get top 10

**Root Cause**: `sorted()` requires O(n log n) to fully sort, then slices last k elements.

**Solution**: Use `heapq.nlargest()` which uses O(n log k) heap:
```python
import heapq
return heapq.nlargest(k, records, key=lambda r: r.get(key, 0))
```

## Git History

- Commit 1 (baseline): heapq.nlargest for O(n log k) - FAST
- Commit 2 (regression): "refactor: use sort-then-slice for top-k clarity" - SLOW
- Commit 3: Add profiling evidence

## ⚠ Misleading Variant Status

The misleading variant for this task is **ineffective**.
The anti-pattern is too obvious: experienced agents immediately find
the correct fix without following the misleading suggestion.
MisleadingGap = 0% in experiments (3/3 misleading runs all passed).

Superseded by ipb_dev_034 which uses the same regex-vs-builtin structure
as ipb_dev_027 (the only confirmed effective misleading task).
