#!/usr/bin/env python3
"""Benchmark: compute_regional_summary performance.

Measures the hot function against the 1.5x speedup threshold defined in
.github/workflows/performance.yml.

Usage:
    python benchmarks/report_bench.py
"""
import statistics
import sys
import timeit
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from daily_report import compute_regional_summary, load_transactions

N_WARMUP = 2
N_RUNS   = 10

print("Generating data …", flush=True)
df = load_transactions()

print(f"Warming up ({N_WARMUP} runs) …", flush=True)
for _ in range(N_WARMUP):
    compute_regional_summary(df)

print(f"Benchmarking ({N_RUNS} runs) …", flush=True)
times = timeit.repeat(lambda: compute_regional_summary(df), number=1, repeat=N_RUNS)

med   = statistics.median(times)
mean  = statistics.mean(times)
stdev = statistics.stdev(times)

print()
print("=== compute_regional_summary ===")
print(f"  Median : {med:.4f}s")
print(f"  Mean   : {mean:.4f}s")
print(f"  Stdev  : {stdev:.4f}s")
print(f"  Min    : {min(times):.4f}s")
print(f"  Max    : {max(times):.4f}s")

# ── threshold check (from .github/workflows/performance.yml) ──────────────────
BASELINE_S  = 0.0952   # measured with groupby.agg before the regression commit
THRESHOLD   = 1.5
required_s  = BASELINE_S * THRESHOLD   # max allowed after fix

print()
print(f"Baseline (pre-regression, groupby.agg) : {BASELINE_S:.4f}s")
print(f"Speedup threshold                      : {THRESHOLD}x")
print(f"Required (median <= {required_s:.4f}s)       : ", end="")
if med <= required_s:
    print(f"PASS  ({med:.4f}s ≤ {required_s:.4f}s)")
else:
    print(f"FAIL  ({med:.4f}s > {required_s:.4f}s)  — needs {med/BASELINE_S:.2f}x speedup vs {THRESHOLD}x target")
