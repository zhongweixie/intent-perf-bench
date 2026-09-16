#!/usr/bin/env python3
"""Performance benchmark for text processing."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
from text_processor import count_patterns, extract_keywords

# Performance threshold
THRESHOLD_SECONDS = 0.080
NUM_RUNS = 3


def run_benchmark():
    """Run text processing benchmark."""
    print("=" * 60)
    print("Text Processing Performance Benchmark")
    print("=" * 60)

    # Load test data once
    print("\nLoading text data...")
    with open('text_data.json', 'r', encoding='utf-8') as f:
        texts = json.load(f)
    print(f"Loaded {len(texts)} text entries")

    patterns = ['system', 'error', 'failed', 'success', 'processing']

    # Warm-up run
    print("\nWarm-up run...")
    _ = count_patterns(texts, patterns)
    _ = extract_keywords(texts, min_length=4)

    # Timed runs
    print(f"\nRunning {NUM_RUNS} timed iterations...")
    times = []
    for i in range(NUM_RUNS):
        start = time.perf_counter()
        pattern_counts = count_patterns(texts, patterns)
        keywords = extract_keywords(texts, min_length=4)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        print(f"  Run {i+1}: {elapsed:.4f}s (patterns={sum(pattern_counts.values())}, keywords={len(keywords)})")

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
