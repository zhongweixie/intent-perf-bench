# Environment

- Python  : 3.11
- pandas  : 3.0.2
- numpy   : 1.26.4
- pyarrow : 18.x (optional, only for Parquet I/O)

## Running the report

```bash
# Dev mode (generates synthetic data in memory)
python scripts/daily_report.py

# With Parquet file
python scripts/daily_report.py --parquet data/transactions.parquet

# Benchmark
python benchmarks/report_bench.py
```

## No repo checkout required

Unlike `ipb_dev_001`, this task does **not** require a library source checkout.
The performance-critical code lives entirely in `scripts/daily_report.py`.
All dependencies are available via `pip install pandas numpy`.
