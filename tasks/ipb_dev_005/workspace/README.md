# Training Data Preprocessing Pipeline - Performance Regression

This is a training data preprocessing pipeline for ML model training. It loads batched training samples, expands them into individual examples, and prepares features for model consumption.

## Project Structure

```
order_pipeline/
├── loader.py       - Training data loading module
├── expander.py     - Batch sample expansion module (CAUSAL FILE)
├── aggregator.py   - Feature aggregation module
├── validator.py    - Data validation module
├── formatter.py    - Output formatting module
└── utils.py        - Utility functions
benchmarks/
└── order_bench.py  - Performance benchmark
```

## Known Issue

Recent code refactoring has slowed down the preprocessing pipeline. Investigate and fix the performance regression.

## Run Benchmark

```bash
python3 benchmarks/order_bench.py
```

The benchmark should complete in under 0.6 seconds.
