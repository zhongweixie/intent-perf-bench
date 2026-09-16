#!/usr/bin/env python3
"""Network analysis pipeline runner."""

import time
from network_analysis import load_graph_data, compute_node_degrees, find_connected_components


def run_pipeline(input_file='graph_data.json'):
    """Run network analysis pipeline with timing."""
    print("=" * 60)
    print("Network Analysis Pipeline")
    print("=" * 60)

    # Stage 1: Load graph data
    print("\n[Stage 1] Loading graph data...")
    start = time.perf_counter()
    graph = load_graph_data(input_file)
    stage1_time = time.perf_counter() - start
    print(f"  Loaded {len(graph['nodes'])} nodes")
    print(f"  Loaded {len(graph['edges'])} edges")
    print(f"  Time: {stage1_time:.4f}s")

    # Stage 2: Compute node degrees
    print("\n[Stage 2] Computing node degrees...")
    start = time.perf_counter()
    degrees = compute_node_degrees(graph)
    stage2_time = time.perf_counter() - start
    max_degree = max(degrees.values())
    avg_degree = sum(degrees.values()) / len(degrees)
    print(f"  Computed degrees for {len(degrees)} nodes")
    print(f"  Max degree: {max_degree}, Avg degree: {avg_degree:.1f}")
    print(f"  Time: {stage2_time:.4f}s")

    # Stage 3: Find connected components
    print("\n[Stage 3] Finding connected components...")
    start = time.perf_counter()
    components = find_connected_components(graph)
    stage3_time = time.perf_counter() - start
    component_sizes = sorted([len(c) for c in components], reverse=True)
    print(f"  Found {len(components)} components")
    print(f"  Largest component: {component_sizes[0]} nodes")
    if len(component_sizes) > 1:
        print(f"  Second largest: {component_sizes[1]} nodes")
    print(f"  Time: {stage3_time:.4f}s")

    # Summary
    total_time = stage1_time + stage2_time + stage3_time
    print("\n" + "=" * 60)
    print("TIMING SUMMARY")
    print("=" * 60)
    print(f"Stage 1 (Load):        {stage1_time:.4f}s ({100*stage1_time/total_time:5.1f}%)")
    print(f"Stage 2 (Degrees):     {stage2_time:.4f}s ({100*stage2_time/total_time:5.1f}%)")
    print(f"Stage 3 (Components):  {stage3_time:.4f}s ({100*stage3_time/total_time:5.1f}%)")
    print("─" * 60)
    print(f"Total:                 {total_time:.4f}s")


if __name__ == '__main__':
    run_pipeline()
