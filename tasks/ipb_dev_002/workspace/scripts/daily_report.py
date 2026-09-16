#!/usr/bin/env python3
"""Daily sales report generator.

Processes transaction data for 1 000 store locations and generates
per-store KPI summary for the operations dashboard.

Usage:
    python daily_report.py
    python daily_report.py --parquet data/transactions.parquet
"""
import argparse
import time

import numpy as np
import pandas as pd

# ── Production dataset dimensions ─────────────────────────────────────────────
N_ROWS   = 3_000_000
N_STORES = 1_000


def load_transactions(path: str = None) -> pd.DataFrame:
    """Load transaction data.

    If *path* is given, reads a Parquet file (production mode).
    Otherwise generates a deterministic synthetic dataset matching the
    production schema (dev / CI mode).
    """
    if path is not None:
        return pd.read_parquet(path)

    rng = np.random.default_rng(2024)
    return pd.DataFrame({
        "transaction_id": np.arange(N_ROWS, dtype=np.int64),
        "store_id":       rng.integers(0, N_STORES, N_ROWS).astype(np.int32),
        "amount":         rng.exponential(120.0, N_ROWS).round(2),
        "units":          rng.integers(1, 10, N_ROWS).astype(np.int16),
        "returned":       (rng.random(N_ROWS) < 0.05).astype(bool),
    })


def compute_regional_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-store KPIs for the daily operations report.

    Returns a DataFrame indexed by store_id with columns:
        total_revenue, order_count, avg_order_value, total_units, return_rate

    Constructs result DataFrame directly from grouped aggregations to
    minimize intermediate Series construction overhead.
    """
    grouped = df.groupby("store_id", observed=True)
    return pd.DataFrame({
        "total_revenue": grouped["amount"].sum(),
        "order_count": grouped["amount"].size(),
        "avg_order_value": grouped["amount"].mean(),
        "total_units": grouped["units"].sum(),
        "return_rate": grouped["returned"].mean(),
    })


def generate_daily_report(df: pd.DataFrame = None) -> dict:
    """Generate the daily report and return summary metrics."""
    if df is None:
        df = load_transactions()

    t0 = time.perf_counter()
    summary = compute_regional_summary(df)
    t1 = time.perf_counter()

    top_stores       = summary.nlargest(10, "total_revenue").index.tolist()
    high_return      = summary[summary["return_rate"] > 0.10].index.tolist()

    return {
        "store_count":             len(summary),
        "total_revenue":           summary["total_revenue"].sum(),
        "top_stores":              top_stores,
        "high_return_rate_stores": high_return,
        "_compute_time_s":         t1 - t0,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--parquet", default=None, help="Path to transactions.parquet")
    args = parser.parse_args()

    t_start = time.perf_counter()
    df     = load_transactions(args.parquet)
    result = generate_daily_report(df)
    t_end  = time.perf_counter()

    print(f"Report generated in {t_end - t_start:.3f}s")
    print(f"  compute_regional_summary : {result['_compute_time_s']:.3f}s")
    print(f"  Total stores             : {result['store_count']}")
    print(f"  Total revenue            : ${result['total_revenue']:,.2f}")
    print(f"  Top-10 stores            : {result['top_stores']}")
    if result["high_return_rate_stores"]:
        print(f"  High-return stores       : {result['high_return_rate_stores'][:5]} ...")
