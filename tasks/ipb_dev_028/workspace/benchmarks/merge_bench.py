#!/usr/bin/env python3
"""Performance benchmark for data merging."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
from data_merger import merge_datasets, deduplicate_records

THRESHOLD_SECONDS = 0.25
NUM_RUNS = 3


def run_benchmark():
    print("=" * 60)
    print("Data Merging Performance Benchmark")
    print("=" * 60)

    print("\nLoading test datasets...")
    with open('test_datasets.json', 'r', encoding='utf-8') as f:
        datasets = json.load(f)
    total_records = sum(len(ds) for ds in datasets)
    print(f"Loaded {len(datasets)} datasets with {total_records} total records")

    # Merge first
    merged = merge_datasets(datasets)
    print(f"Merged to {len(merged)} records")

    # Quick probe on small subset to detect O(n²)
    probe_size = 1000
    probe_records = merged[:probe_size]
    t0 = time.perf_counter()
    deduplicate_records(probe_records)
    probe_time = time.perf_counter() - t0
    n_full = len(merged)
    estimated_full = probe_time * (n_full / probe_size) ** 2

    print(f"\nProbe ({probe_size} records): {probe_time:.4f}s")
    print(f"Estimated full ({n_full} records): {estimated_full:.1f}s")

    if estimated_full > THRESHOLD_SECONDS * 10:
        print(f"\n✗ FAIL: Estimated time {estimated_full:.1f}s far exceeds threshold {THRESHOLD_SECONDS}s (O(n²) detected)")
        return 1

    # Full timed runs
    print(f"\nRunning {NUM_RUNS} timed iterations...")
    times = []
    for i in range(NUM_RUNS):
        m = merge_datasets(datasets)
        start = time.perf_counter()
        unique = deduplicate_records(m)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        print(f"  Run {i+1}: {elapsed:.4f}s (merged={len(m)}, unique={len(unique)})")

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
