#!/usr/bin/env python3
"""Performance benchmark for cache system."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
from cache_manager import get_cached, set_cached, clear_cache
from cache_manager.cache_ops import cache_stats

# Performance threshold
THRESHOLD_SECONDS = 0.015
NUM_RUNS = 3


def expensive_lookup(key, source_data):
    """Simulate expensive data lookup operation."""
    _ = [i**2 for i in range(100)]
    return source_data.get(key)


def run_benchmark():
    """Run cache system benchmark."""
    print("=" * 60)
    print("Cache System Performance Benchmark")
    print("=" * 60)

    # Load test data
    print("\nLoading test data...")
    with open('queries.json', 'r', encoding='utf-8') as f:
        queries = json.load(f)
    with open('source_data.json', 'r', encoding='utf-8') as f:
        source_data = json.load(f)
    print(f"Loaded {len(queries)} queries, {len(source_data)} source records")

    # Warm-up run
    print("\nWarm-up run...")
    clear_cache()
    for query_key in queries:
        cached_value = get_cached(query_key)
        if cached_value is None:
            value = expensive_lookup(query_key, source_data)
            set_cached(query_key, value)

    # Check cache correctness: capacity must be respected
    stats = cache_stats()
    print(f"\nCache stats after warm-up:")
    print(f"  Size:     {stats['size']}")
    print(f"  Capacity: {stats['capacity']}")
    print(f"  Hit rate: {stats['hit_rate']:.1%}")

    capacity_violated = stats['size'] > stats['capacity']

    # Timed runs
    print(f"\nRunning {NUM_RUNS} timed iterations...")
    times = []

    for i in range(NUM_RUNS):
        clear_cache()
        start = time.perf_counter()

        results = []
        for query_key in queries:
            cached_value = get_cached(query_key)
            if cached_value is not None:
                results.append(cached_value)
            else:
                value = expensive_lookup(query_key, source_data)
                set_cached(query_key, value)
                results.append(value)

        elapsed = time.perf_counter() - start
        times.append(elapsed)
        print(f"  Run {i + 1}: {elapsed:.4f}s ({len(results)} lookups)")

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

    # Fail if either performance threshold exceeded OR capacity violated
    perf_fail = best_time > THRESHOLD_SECONDS
    if capacity_violated:
        print(f"✗ FAIL: Cache capacity violated ({stats['size']} > {stats['capacity']})")
        return 1
    elif perf_fail:
        print(f"✗ FAIL: Performance exceeds threshold by {best_time - THRESHOLD_SECONDS:.4f}s")
        return 1
    else:
        print("✓ PASS: Performance within threshold and cache capacity respected")
        return 0


if __name__ == '__main__':
    exit(run_benchmark())
