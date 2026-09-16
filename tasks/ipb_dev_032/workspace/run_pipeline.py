#!/usr/bin/env python3
"""Run metric collection pipeline with timing."""

import json
import time
from metric_collector import collect_metrics, compute_percentiles


def run_pipeline():
    print("=" * 60)
    print("Metric Collection Pipeline")
    print("=" * 60)

    print("\n[Stage 1] Loading samples...")
    start = time.perf_counter()
    with open('test_metrics.json', 'r', encoding='utf-8') as f:
        samples = json.load(f)
    stage1_time = time.perf_counter() - start
    print(f"  Loaded {len(samples)} samples")
    print(f"  Time: {stage1_time:.4f}s")

    print("\n[Stage 2] Collecting metrics...")
    start = time.perf_counter()
    metrics = collect_metrics(samples)
    stage2_time = time.perf_counter() - start
    print(f"  Collected {len(metrics)} metrics")
    print(f"  Time: {stage2_time:.4f}s")

    print("\n[Stage 3] Computing percentiles...")
    values = [m['value'] for m in metrics]
    start = time.perf_counter()
    pctls = compute_percentiles(values)
    stage3_time = time.perf_counter() - start
    print(f"  p50={pctls[50]:.1f}, p90={pctls[90]:.1f}, p95={pctls[95]:.1f}, p99={pctls[99]:.1f}")
    print(f"  Time: {stage3_time:.4f}s")

    total_time = stage1_time + stage2_time + stage3_time
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Stage 1 (Load):        {stage1_time:.4f}s")
    print(f"  Stage 2 (Collect):     {stage2_time:.4f}s")
    print(f"  Stage 3 (Percentiles): {stage3_time:.4f}s")
    print(f"  Total:                 {total_time:.4f}s")


if __name__ == '__main__':
    run_pipeline()
