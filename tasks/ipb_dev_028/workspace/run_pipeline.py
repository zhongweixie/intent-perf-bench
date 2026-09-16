#!/usr/bin/env python3
"""Run data merging pipeline with timing."""

import json
import time
from data_merger import merge_datasets, deduplicate_records


def run_pipeline():
    """Run data merging pipeline with timing."""
    print("=" * 60)
    print("Data Merging Pipeline")
    print("=" * 60)

    # Stage 1: Load datasets
    print("\n[Stage 1] Loading datasets...")
    start = time.perf_counter()
    with open('test_datasets.json', 'r', encoding='utf-8') as f:
        datasets = json.load(f)
    stage1_time = time.perf_counter() - start
    total_records = sum(len(ds) for ds in datasets)
    print(f"  Loaded {len(datasets)} datasets with {total_records} total records")
    print(f"  Time: {stage1_time:.4f}s")

    # Stage 2: Merge datasets
    print("\n[Stage 2] Merging datasets...")
    start = time.perf_counter()
    merged = merge_datasets(datasets)
    stage2_time = time.perf_counter() - start
    print(f"  Merged into {len(merged)} records")
    print(f"  Time: {stage2_time:.4f}s")

    # Stage 3: Deduplicate
    print("\n[Stage 3] Deduplicating records...")
    start = time.perf_counter()
    unique = deduplicate_records(merged)
    stage3_time = time.perf_counter() - start
    duplicates_removed = len(merged) - len(unique)
    print(f"  Unique records: {len(unique)}")
    print(f"  Duplicates removed: {duplicates_removed}")
    print(f"  Time: {stage3_time:.4f}s")

    # Summary
    total_time = stage1_time + stage2_time + stage3_time
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Stage 1 (Load):    {stage1_time:.4f}s")
    print(f"  Stage 2 (Merge):   {stage2_time:.4f}s")
    print(f"  Stage 3 (Dedup):   {stage3_time:.4f}s")
    print(f"  Total:             {total_time:.4f}s")
    print("=" * 60)


if __name__ == '__main__':
    run_pipeline()
