#!/usr/bin/env python3
"""Performance benchmark for CSV processing pipeline."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import time
import os
from csv_processor import parse_csv_file, analyze_data

# Performance threshold
THRESHOLD_SECONDS = 0.21
NUM_RUNS = 3


def run_benchmark():
    """Run CSV processing benchmark."""
    print("=" * 60)
    print("CSV Processing Performance Benchmark")
    print("=" * 60)

    # Verify data file exists
    if not os.path.exists('sample_data.csv'):
        print("\nERROR: sample_data.csv not found")
        print("Run: python3 generate_data.py")
        return 1

    # Warm-up run
    print("\nWarm-up run...")
    records = parse_csv_file('sample_data.csv')
    _ = analyze_data(records)
    print(f"Loaded {len(records)} records")

    # Timed runs
    print(f"\nRunning {NUM_RUNS} timed iterations...")
    times = []

    for i in range(NUM_RUNS):
        start = time.perf_counter()
        records = parse_csv_file('sample_data.csv')
        analysis = analyze_data(records)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        print(f"  Run {i+1}: {elapsed:.4f}s")

    # Results
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
        excess = best_time - THRESHOLD_SECONDS
        print(f"✗ FAIL: Performance exceeds threshold by {excess:.4f}s")
        return 1


if __name__ == '__main__':
    exit(run_benchmark())
