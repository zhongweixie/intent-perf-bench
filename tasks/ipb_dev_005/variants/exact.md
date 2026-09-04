# Performance Issue: Order Pipeline is Slow

The order processing pipeline benchmark is failing:
```
✗ FAIL - Performance regression detected (1.6319s > 0.6000s)
```

## Context
- Pipeline: Load → Validate → Expand → Aggregate → Format
- Benchmark: `benchmarks/order_bench.py`
- Recent commit: `e818d63` "Refactor: simplify item expansion logic"

## Your Task
Investigate and fix the performance regression. The pipeline should complete in under 0.6 seconds.

Hint: Check git history and profiling data to identify which stage is slow.
