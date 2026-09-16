#!/usr/bin/env python3
"""Performance benchmark for metric collection."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
from metric_collector import collect_metrics, compute_percentiles

THRESHOLD_SECONDS = 0.10
NUM_RUNS = 3


def run_benchmark():
    print("=" * 60)
    print("Metric Collection Performance Benchmark")
    print("=" * 60)

    print("\nLoading test data...")
    with open('test_metrics.json', 'r', encoding='utf-8') as f:
        samples = json.load(f)
    print(f"Loaded {len(samples)} samples")

    print("\nCollecting metrics...")
    metrics = collect_metrics(samples)
    values = [m['value'] for m in metrics]
    print(f"Collected {len(metrics)} metrics")

    print("\nWarm-up run...")
    _ = compute_percentiles(values)

    print(f"\nRunning {NUM_RUNS} timed iterations...")
    times = []
    for i in range(NUM_RUNS):
        start = time.perf_counter()
        pctls = compute_percentiles(values)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        print(f"  Run {i+1}: {elapsed:.4f}s (p50={pctls[50]:.1f}, p99={pctls[99]:.1f})")

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
