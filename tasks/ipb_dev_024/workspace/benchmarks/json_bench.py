#!/usr/bin/env python3
"""Performance benchmark for JSON processing."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from json_processor import parse_records, extract_fields

# Performance threshold
THRESHOLD_SECONDS = 0.050
NUM_RUNS = 3


def run_benchmark():
    """Run JSON processing benchmark."""
    print("=" * 60)
    print("JSON Processing Performance Benchmark")
    print("=" * 60)

    # Load test data once
    print("\nLoading test data...")
    with open('test_data.json', 'r', encoding='utf-8') as f:
        json_string = f.read()

    print("\nParsing JSON...")
    records = parse_records(json_string)
    print(f"Loaded {len(records)} records")

    field_names = ['id', 'timestamp', 'value', 'status']

    # Warm-up run
    print("\nWarm-up run...")
    _ = extract_fields(records, field_names)

    # Timed runs
    print(f"\nRunning {NUM_RUNS} timed iterations...")
    times = []
    for i in range(NUM_RUNS):
        start = time.perf_counter()
        result = extract_fields(records, field_names)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        print(f"  Run {i+1}: {elapsed:.4f}s ({len(result)} records extracted)")

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
