# Performance Issue: Inventory Management Pipeline is Slow

The inventory pipeline benchmark is failing:
```
✗ FAIL - Performance regression detected (3.1468s > 0.08s)
```

## Context
- Pipeline: Load → Check Reorder Status → Aggregate
- Benchmark: `benchmarks/inv_bench.py`
- Recent commit: `efcad98`

## Your Task
Investigate and fix the performance regression. Use profiling_data.txt and git.log to guide your investigation.

Run `python3 benchmarks/inv_bench.py` to validate performance.
