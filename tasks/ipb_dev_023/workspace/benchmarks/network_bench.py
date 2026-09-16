#!/usr/bin/env python3
"""Performance benchmark for network analysis."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import time
from network_analysis import load_graph_data, find_connected_components

# Performance threshold
THRESHOLD_SECONDS = 0.12
NUM_RUNS = 3


def run_benchmark():
    """Run network analysis benchmark."""
    print("=" * 60)
    print("Network Analysis Performance Benchmark")
    print("=" * 60)

    # Load test data once
    print("\nLoading test graph data...")
    graph = load_graph_data('graph_data.json')
    print(f"Loaded {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")

    # Warm-up run
    print("\nWarm-up run...")
    _ = find_connected_components(graph)

    # Timed runs
    print(f"\nRunning {NUM_RUNS} timed iterations...")
    times = []

    for i in range(NUM_RUNS):
        start = time.perf_counter()
        components = find_connected_components(graph)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        print(f"  Run {i + 1}: {elapsed:.4f}s ({len(components)} components found)")

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

    if best_time <= THRESHOLD_SECONDS:
        print("✓ PASS: Performance within threshold")
        return 0
    else:
        print(f"✗ FAIL: Performance exceeds threshold by {best_time - THRESHOLD_SECONDS:.4f}s")
        return 1


if __name__ == '__main__':
    exit(run_benchmark())
