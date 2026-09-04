# Performance Issue: Order Pipeline is Slow

The order processing pipeline benchmark is failing:
```
✗ FAIL - Performance regression detected (1.6319s > 0.6000s)
```

## Context
- Pipeline: Load → Validate → Expand → Aggregate → Format
- The Expand stage in `order_pipeline/expander.py` is suspected to be slow
- Recent commit: "Refactor: simplify item expansion logic"

## Your Task
Investigate and fix the performance issue in the Expand stage. The pipeline should complete in under 0.6 seconds.
