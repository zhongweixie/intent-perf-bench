#!/usr/bin/env python3
"""Performance benchmark for validation."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
from validator import validate_records, check_constraints

# Performance threshold
THRESHOLD_SECONDS = 0.025
NUM_RUNS = 3


def run_benchmark():
    """Run validation benchmark."""
    print("=" * 60)
    print("Validation Performance Benchmark")
    print("=" * 60)

    # Load test data once
    print("\nLoading test data...")
    with open('test_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"Loaded {len(data)} records")

    # Validate once
    print("\nValidating records...")
    valid = validate_records(data)
    print(f"Valid records: {len(valid)}")

    # Warm-up run
    print("\nWarm-up run...")
    _ = check_constraints(valid)

    # Timed runs
    print(f"\nRunning {NUM_RUNS} timed iterations...")
    times = []
    for i in range(NUM_RUNS):
        start = time.perf_counter()
        pass_count, fail_count = check_constraints(valid)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        print(f"  Run {i+1}: {elapsed:.4f}s (pass={pass_count}, fail={fail_count})")

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
