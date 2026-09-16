#!/usr/bin/env python3
"""Run data processing pipeline with timing."""

import json
import time
from data_processor import filter_records, compute_statistics


def run_pipeline():
    """Run data processing pipeline with timing."""
    print("=" * 60)
    print("Data Processing Pipeline")
    print("=" * 60)

    # Stage 1: Load data
    print("\n[Stage 1] Loading test data...")
    start = time.perf_counter()
    with open('test_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    stage1_time = time.perf_counter() - start
    print(f"  Loaded {len(data)} records")
    print(f"  Time: {stage1_time:.4f}s")

    # Stage 2: Filter records
    print("\n[Stage 2] Filtering records...")
    start = time.perf_counter()
    filtered = filter_records(data, threshold=500)
    stage2_time = time.perf_counter() - start
    print(f"  Filtered to {len(filtered)} records (threshold > 500)")
    print(f"  Time: {stage2_time:.4f}s")

    # Stage 3: Compute statistics
    print("\n[Stage 3] Computing statistics...")
    start = time.perf_counter()
    stats = compute_statistics(filtered)
    stage3_time = time.perf_counter() - start
    print(f"  Computed stats for {len(stats)} categories")
    print(f"  Time: {stage3_time:.4f}s")

    # Summary
    total_time = stage1_time + stage2_time + stage3_time
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Stage 1 (Load):    {stage1_time:.4f}s")
    print(f"  Stage 2 (Filter):  {stage2_time:.4f}s")
    print(f"  Stage 3 (Stats):   {stage3_time:.4f}s")
    print(f"  Total:             {total_time:.4f}s")
    print("=" * 60)


if __name__ == '__main__':
    run_pipeline()
