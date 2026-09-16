#!/usr/bin/env python3
"""Performance benchmark for query engine."""

import json
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import time
from query_engine import build_index, apply_filters, search_records

# Performance threshold (tighter)
THRESHOLD_SECONDS = 0.070
NUM_RUNS = 3


def run_benchmark():
    """Run query engine benchmark."""
    print("=" * 60)
    print("Query Engine Performance Benchmark")
    print("=" * 60)

    # Load test data
    print("\nLoading test data...")
    with open('records.json', 'r', encoding='utf-8') as f:
        records = json.load(f)
    print(f"Loaded {len(records)} records")

    # Warm-up run
    print("\nWarm-up run...")
    index = build_index(records)
    _ = apply_filters(index, {'category': 'Electronics'})
    _ = apply_filters(index, {'status': 'active'})
    _ = apply_filters(index, {'category': 'Books', 'status': 'pending'})
    _ = search_records(records, ['Product', '00042'])

    # Timed runs
    print(f"\nRunning {NUM_RUNS} timed iterations...")
    times = []

    for i in range(NUM_RUNS):
        start = time.perf_counter()

        index = build_index(records)
        r1 = apply_filters(index, {'category': 'Electronics'})
        r2 = apply_filters(index, {'status': 'active'})
        r3 = apply_filters(index, {'category': 'Books', 'status': 'pending'})
        r4 = search_records(records, ['Product', '00042'])

        elapsed = time.perf_counter() - start
        times.append(elapsed)
        print(f"  Run {i + 1}: {elapsed:.4f}s")

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
        print(f"✗ FAIL: Performance exceeds threshold by {best_time - THRESHOLD_SECONDS:.4f}s")
        return 1


if __name__ == '__main__':
    exit(run_benchmark())
