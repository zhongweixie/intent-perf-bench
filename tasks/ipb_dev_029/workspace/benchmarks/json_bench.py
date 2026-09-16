#!/usr/bin/env python3
"""Performance benchmark for JSON processing."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from json_processor import parse_json_stream, extract_nested_values

# Performance threshold
THRESHOLD_SECONDS = 0.080
NUM_RUNS = 3


def run_benchmark():
    """Run JSON processing benchmark."""
    print("=" * 60)
    print("JSON Processing Performance Benchmark")
    print("=" * 60)

    # Load test data once
    print("\nLoading test data...")
    with open('test_data.jsonl', 'r', encoding='utf-8') as f:
        json_lines = [line.strip() for line in f if line.strip()]
    print(f"Loaded {len(json_lines)} JSON lines")

    print("\nParsing JSON...")
    objects = parse_json_stream(json_lines)
    print(f"Parsed {len(objects)} objects")

    # Warm-up run
    print("\nWarm-up run...")
    _ = extract_nested_values(objects, 'user.profile.name')
    _ = extract_nested_values(objects, 'data.metrics.cpu')

    # Timed runs
    print(f"\nRunning {NUM_RUNS} timed iterations...")
    times = []
    for i in range(NUM_RUNS):
        start = time.perf_counter()
        names = extract_nested_values(objects, 'user.profile.name')
        emails = extract_nested_values(objects, 'user.profile.email')
        cpu_metrics = extract_nested_values(objects, 'data.metrics.cpu')
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        print(f"  Run {i+1}: {elapsed:.4f}s ({len(names)} names, {len(cpu_metrics)} cpu values)")

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
