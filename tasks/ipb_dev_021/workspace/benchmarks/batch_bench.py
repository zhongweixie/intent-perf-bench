#!/usr/bin/env python3
"""Performance benchmark for batch processing."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from data_processor import load_records, process_batch

THRESHOLD_SECONDS = 0.08
NUM_RUNS = 3


def run_benchmark():
    print("=" * 60)
    print("Batch Processing Performance Benchmark")
    print("=" * 60)

    print("\nLoading test data...")
    records = load_records('test_data.json')
    print(f"Loaded {len(records)} records")

    # Probe on 200 records to detect O(n²)
    probe_size = 200
    probe = records[:probe_size]
    t0 = time.perf_counter()
    _ = process_batch(probe)
    probe_time = time.perf_counter() - t0
    n_full = len(records)
    estimated_full = probe_time * (n_full / probe_size) ** 2

    print(f"\nProbe ({probe_size} records): {probe_time:.4f}s")
    print(f"Estimated full ({n_full} records): {estimated_full:.1f}s")

    if estimated_full > THRESHOLD_SECONDS * 10:
        print(f"\n✗ FAIL: Estimated time {estimated_full:.1f}s far exceeds threshold (O(n²) detected)")
        return 1

    # Full timed runs
    print(f"\nRunning {NUM_RUNS} timed iterations...")
    times = []
    for i in range(NUM_RUNS):
        start = time.perf_counter()
        processed = process_batch(records)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        print(f"  Run {i+1}: {elapsed:.4f}s ({len(processed)} unique records)")

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
