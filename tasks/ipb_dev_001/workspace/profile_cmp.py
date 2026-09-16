"""
Profile the _cmp_method to identify the bottleneck.
"""
import pandas as pd
import numpy as np
import cProfile
import pstats
from io import StringIO
import sys

# Generate test data
n_rows = 10_000_000
print(f"Generating {n_rows:,} rows of test data...", file=sys.stderr)

rng = np.random.default_rng(42)
base = pd.date_range("2024-01-01", periods=n_rows, freq="ms")

df = pd.DataFrame({
    "tx_time":  base,
    "deadline": base + pd.to_timedelta(rng.integers(1, 3601, size=n_rows), unit="s"),
})

print(f"Data generated. Profiling comparison...", file=sys.stderr)

# Profile the comparison
pr = cProfile.Profile()
pr.enable()
violations = df["tx_time"] > df["deadline"]
pr.disable()

# Print stats
s = StringIO()
ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
ps.print_stats(20)
print(s.getvalue())
