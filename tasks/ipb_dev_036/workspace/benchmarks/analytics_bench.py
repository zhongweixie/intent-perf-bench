#!/usr/bin/env python3
"""Performance benchmark for order analytics pipeline."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from order_analytics import load_orders, build_user_report

THRESHOLD_SECONDS = 0.25
NUM_RUNS = 3


def run_benchmark():
    print("=" * 60)
    print("Order Analytics Performance Benchmark")
    print("=" * 60)

    print("\nLoading orders...")
    t0 = time.perf_counter()
    orders = load_orders()
    t_load = time.perf_counter() - t0
    print(f"  Loaded {len(orders)} orders in {t_load:.3f}s")

    print("\nWarm-up run...")
    _ = build_user_report(orders)

    print(f"\nRunning {NUM_RUNS} timed iterations...")
    times = []
    for i in range(NUM_RUNS):
        start = time.perf_counter()
        report = build_user_report(orders)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        print(f"  Run {i+1}: {elapsed:.4f}s ({len(report)} users in report)")

    best_time = min(times)
    avg_time = sum(times) / len(times)

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Best time:    {best_time:.4f}s")
    print(f"Average time: {avg_time:.4f}s")
    print(f"Threshold:    {THRESHOLD_SECONDS:.4f}s")
    print()

    if best_time <= THRESHOLD_SECONDS:
        print("✓ PASS: Performance within threshold")
        return 0
    else:
        print(f"✗ FAIL: Exceeded threshold by {(best_time - THRESHOLD_SECONDS):.4f}s")
        return 1


if __name__ == '__main__':
    exit(run_benchmark())
