#!/usr/bin/env python3
"""Performance benchmark for log analysis."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from log_analyzer import parse_log_lines, count_error_types

THRESHOLD_SECONDS = 0.025
NUM_RUNS = 3


def run_benchmark():
    print("=" * 60)
    print("Log Analysis Performance Benchmark")
    print("=" * 60)

    print("\nLoading test data...")
    with open('test_logs.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    print(f"Loaded {len(lines)} log lines")

    print("\nParsing logs...")
    log_entries = parse_log_lines(lines)
    print(f"Parsed {len(log_entries)} entries")

    print("\nWarm-up run...")
    _ = count_error_types(log_entries)

    print(f"\nRunning {NUM_RUNS} timed iterations...")
    times = []
    for i in range(NUM_RUNS):
        start = time.perf_counter()
        counts = count_error_types(log_entries)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        total = sum(counts.values())
        print(f"  Run {i+1}: {elapsed:.4f}s ({total} entries, {len(counts)} levels)")

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
