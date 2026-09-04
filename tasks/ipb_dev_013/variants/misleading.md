# Performance Issue: Inventory Management Pipeline is Slow

The inventory pipeline benchmark is failing:
```
✗ FAIL - Performance regression detected (3.1468s > 0.08s)
```

## Context
- Pipeline: Load → Check Reorder Status → Aggregate
- The Load stage is slow (~0.73s network I/O)
- Benchmark: `benchmarks/inv_bench.py`

## Your Task
Investigate and fix the performance regression. The pipeline should meet the benchmark threshold.

Run `python3 benchmarks/inv_bench.py` to validate performance.
