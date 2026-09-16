# Development Environment

## System Information
- Python: 3.11+
- OS: Linux/macOS

## Dependencies
```bash
pip install pandas numpy pyarrow
```

## Package Versions (tested)
- pandas: 2.0.0+
- numpy: 1.24.0+
- pyarrow: 12.0.0+

## Data Generation
```bash
python3 generate_data.py
```
Generates `data/transactions.parquet` with 100,000 synthetic transactions.

## Running the Pipeline
```bash
python3 run_pipeline.py
```

## Performance Benchmark
```bash
python3 benchmarks/pipeline_bench.py
```

Expected baseline performance: ~0.15s median (100k transactions)
Performance threshold: 1.0s (1.5x regression tolerance + I/O variance)

## CI/CD
GitHub Actions workflow runs performance tests on every push.
See `.github/workflows/performance.yml`

## Performance Notes
- Transform stage is the most performance-sensitive
- Use vectorized pandas operations (groupby, cumsum, etc.)
- Avoid iterrows() for large datasets - causes O(n²) complexity
- Export stage may show I/O variance (0.05s - 1.2s) depending on disk cache
