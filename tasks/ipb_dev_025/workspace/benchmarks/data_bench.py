#!/usr/bin/env python3
"""Performance benchmark for data processing."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
from data_processor import filter_records, compute_statistics

# Performance threshold
THRESHOLD_SECONDS = 0.040
NUM_RUNS = 3


def run_benchmark():
    """Run data processing benchmark."""
    print("=" * 60)
    print("Data Processing Performance Benchmark")
    print("=" * 60)

    # Load test data once
    print("\nLoading test data...")
    with open('test_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"Loaded {len(data)} records")

    # Filter once
    print("\nFiltering records...")
    filtered = filter_records(data, threshold=500)
    print(f"Filtered to {len(filtered)} records")

    # Warm-up run
    print("\nWarm-up run...")
    _ = compute_statistics(filtered)

    # Timed runs
    print(f"\nRunning {NUM_RUNS} timed iterations...")
    times = []
    for i in range(NUM_RUNS):
        start = time.perf_counter()
        stats = compute_statistics(filtered)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        print(f"  Run {i+1}: {elapsed:.4f}s ({len(stats)} categories)")

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
