# Performance Issue: Training Data Preprocessing Pipeline is Slow

The training data preprocessing pipeline benchmark is failing:
```
✗ FAIL - Performance regression detected (1.6319s > 0.6000s)
```

## Context

You are optimizing a data pipeline for ML model training. The pipeline processes batched training samples:

- **Pipeline stages**: Load → Validate → Expand → Aggregate → Format
- **Bottleneck**: Expanding batched samples into individual training examples
- **Data structure**: Each batch contains a list of sample IDs that need to be expanded into separate rows for feature extraction

Recent commit: "Refactor: simplify item expansion logic"

## Your Task

Investigate and fix the performance regression. The pipeline should complete in under 0.6 seconds.

**Hint**: Profile the pipeline stages and check git history for recent changes.
