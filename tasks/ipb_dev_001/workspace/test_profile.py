"""
Profile script to measure the comparison operation without parquet dependency.
"""
import pandas as pd
import numpy as np
import time
import sys

# Generate test data similar to daily_report.py
n_rows = 10_000_000
print(f"Generating {n_rows:,} rows of test data...", file=sys.stderr)

rng = np.random.default_rng(42)
base = pd.date_range("2024-01-01", periods=n_rows, freq="ms")

df = pd.DataFrame({
    "tx_time":  base,
    "deadline": base + pd.to_timedelta(rng.integers(1, 3601, size=n_rows), unit="s"),
})

print(f"Data generated. Starting comparison benchmark...", file=sys.stderr)

# Time the comparison operation (this is the bottleneck)
t0 = time.perf_counter()
violations = df["tx_time"] > df["deadline"]
elapsed = time.perf_counter() - t0

print(f"\nComparison time: {elapsed:.4f}s")
print(f"Violations found: {violations.sum()} / {len(violations)}")
