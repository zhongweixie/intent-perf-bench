# Performance Issue: Training Data Preprocessing Pipeline is Slow

The training data preprocessing pipeline benchmark is failing:
```
✗ FAIL - Performance regression detected (1.6319s > 0.6000s)
```

## Context

You are optimizing a data pipeline for ML model training. The pipeline processes batched training samples:

- **Pipeline stages**: Load → Validate → Expand → Aggregate → Format
- **Observed**: The validation stage seems to be performing redundant checks
- **Data structure**: Training batches with sample ID lists that need expansion
- **Benchmark**: `benchmarks/order_bench.py`

## Your Task

Investigate and fix the performance regression. The pipeline should complete in under 0.6 seconds.

**Note**: The validation logic may be running inefficiently, potentially checking the same conditions multiple times or using slow data structures. Consider optimizing the validation rules or restructuring how checks are performed.
