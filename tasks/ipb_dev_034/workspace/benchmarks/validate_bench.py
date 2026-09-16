#!/usr/bin/env python3
"""Performance benchmark for CSV field validation."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from csv_validator import load_csv_fields, validate_fields

THRESHOLD_SECONDS = 0.070
NUM_RUNS = 3


def run_benchmark():
    print("=" * 60)
    print("CSV Validation Performance Benchmark")
    print("=" * 60)

    print("\nLoading test data...")
    fields = load_csv_fields('test_fields.json')
    print(f"Loaded {len(fields):,} fields")

    print("\nWarm-up run...")
    _ = validate_fields(fields)

    print(f"\nRunning {NUM_RUNS} timed iterations...")
    times = []
    for i in range(NUM_RUNS):
        start = time.perf_counter()
        results = validate_fields(fields)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        print(f"  Run {i+1}: {elapsed:.4f}s ({sum(results):,} numeric)")

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
        print(f"✗ FAIL: Exceeded threshold by {best_time - THRESHOLD_SECONDS:.4f}s")
        return 1


if __name__ == '__main__':
    exit(run_benchmark())
