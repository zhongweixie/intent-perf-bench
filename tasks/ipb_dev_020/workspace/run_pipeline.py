#!/usr/bin/env python3
"""Cache system pipeline runner."""

import json
import time
from cache_manager import get_cached, set_cached, clear_cache
from cache_manager.cache_ops import cache_stats


def expensive_lookup(key, source_data):
    """Simulate expensive data lookup operation.

    Args:
        key: Lookup key
        source_data: Full dataset

    Returns:
        Value from source data
    """
    # Simulate some processing overhead
    _ = [i**2 for i in range(100)]
    return source_data.get(key)


def run_pipeline(queries_file='queries.json', data_file='source_data.json'):
    """Run cache system pipeline with timing."""
    print("=" * 60)
    print("Cache System Pipeline")
    print("=" * 60)

    # Stage 1: Load data
    print("\n[Stage 1] Loading data...")
    start = time.perf_counter()
    with open(queries_file, 'r', encoding='utf-8') as f:
        queries = json.load(f)
    with open(data_file, 'r', encoding='utf-8') as f:
        source_data = json.load(f)
    stage1_time = time.perf_counter() - start
    print(f"  Loaded {len(queries)} queries")
    print(f"  Loaded {len(source_data)} source records")
    print(f"  Time: {stage1_time:.4f}s")

    # Stage 2: Process lookups with cache
    print("\n[Stage 2] Processing lookups...")
    clear_cache()
    start = time.perf_counter()

    results = []
    for query_key in queries:
        # Check cache first
        cached_value = get_cached(query_key)
        if cached_value is not None:
            results.append(cached_value)
        else:
            # Cache miss - expensive lookup
            value = expensive_lookup(query_key, source_data)
            set_cached(query_key, value)
            results.append(value)

    stage2_time = time.perf_counter() - start
    stats = cache_stats()
    print(f"  Processed {len(results)} lookups")
    print(f"  Cache hits: {stats['hits']}, misses: {stats['misses']}")
    print(f"  Hit rate: {stats['hit_rate']:.1%}")
    print(f"  Time: {stage2_time:.4f}s")

    # Summary
    total_time = stage1_time + stage2_time
    print("\n" + "=" * 60)
    print("TIMING SUMMARY")
    print("=" * 60)
    print(f"Stage 1 (Load):        {stage1_time:.4f}s ({100*stage1_time/total_time:5.1f}%)")
    print(f"Stage 2 (Lookup):      {stage2_time:.4f}s ({100*stage2_time/total_time:5.1f}%)")
    print("─" * 60)
    print(f"Total:                 {total_time:.4f}s")


if __name__ == '__main__':
    run_pipeline()
