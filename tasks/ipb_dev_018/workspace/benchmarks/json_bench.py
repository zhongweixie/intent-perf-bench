#!/usr/bin/env python3
"""Performance benchmark for JSON processing."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import time
from json_processor import load_json_files, validate_schema

THRESHOLD_SECONDS = 0.40
NUM_RUNS = 3


def run_benchmark():
    print("=" * 60)
    print("JSON Processing Performance Benchmark")
    print("=" * 60)

    # Load and validate (no merge yet)
    print("\nLoading and validating...")
    records = load_json_files('json_data')
    flattened = []
    for item in records:
        if isinstance(item, list):
            flattened.extend(item)
        else:
            flattened.append(item)
    valid_records, _ = validate_schema(flattened)
    print(f"Loaded {len(valid_records)} valid records")

    # Quick probe: run merge on 500 records to estimate full cost
    from json_processor import merge_records
    probe = valid_records[:500]
    t0 = time.perf_counter()
    merge_records(probe)
    probe_time = time.perf_counter() - t0
    # O(n²) estimate for full 20k
    n_full = len(valid_records)
    estimated_full = probe_time * (n_full / 500) ** 2
    print(f"\nProbe (500 records): {probe_time:.4f}s")
    print(f"Estimated full ({n_full} records): {estimated_full:.1f}s")

    if estimated_full > THRESHOLD_SECONDS * 5:
        print(f"\n✗ FAIL: Estimated time {estimated_full:.1f}s far exceeds threshold {THRESHOLD_SECONDS}s")
        return 1

    # Timed runs (only if probe looks okay)
    print(f"\nRunning {NUM_RUNS} timed iterations...")
    times = []
    for i in range(NUM_RUNS):
        start = time.perf_counter()
        unique_records = merge_records(valid_records)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        print(f"  Run {i + 1}: {elapsed:.4f}s ({len(unique_records)} unique)")

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
