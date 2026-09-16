#!/usr/bin/env python3
"""Performance benchmark for event processing."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
from event_processor import process_events, aggregate_by_type

THRESHOLD_SECONDS = 0.25
NUM_RUNS = 3


def run_benchmark():
    print("=" * 60)
    print("Event Processing Performance Benchmark")
    print("=" * 60)

    print("\nLoading test data...")
    with open('test_events.json', 'r', encoding='utf-8') as f:
        events = json.load(f)
    print(f"Loaded {len(events)} events")

    print("\nWarm-up run...")
    processed = process_events(events)
    _ = aggregate_by_type(processed)

    print(f"\nRunning {NUM_RUNS} timed iterations...")
    times = []
    for i in range(NUM_RUNS):
        start = time.perf_counter()
        processed = process_events(events)
        stats = aggregate_by_type(processed)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        print(f"  Run {i+1}: {elapsed:.4f}s ({len(stats)} types)")

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
