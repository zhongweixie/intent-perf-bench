#!/usr/bin/env python3
"""Performance benchmark for pricing engine."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from pricing_engine import load_orders, calculate_order_totals

THRESHOLD_SECONDS = 0.20
NUM_RUNS = 3


def run_benchmark():
    print("=" * 60)
    print("Pricing Engine Performance Benchmark")
    print("=" * 60)

    print("\nLoading orders...")
    orders = load_orders()
    print(f"Loaded {len(orders)} orders")

    print("\nWarm-up run...")
    _ = calculate_order_totals(orders)

    print(f"\nRunning {NUM_RUNS} timed iterations...")
    times = []
    for i in range(NUM_RUNS):
        start = time.perf_counter()
        results = calculate_order_totals(orders)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        print(f"  Run {i+1}: {elapsed:.4f}s ({len(results)} orders processed)")

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
