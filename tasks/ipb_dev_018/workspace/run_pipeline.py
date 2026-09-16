#!/usr/bin/env python3
"""JSON processing pipeline runner."""

import time
from json_processor import load_json_files, merge_records, validate_schema


def run_pipeline(data_dir='json_data'):
    """Run JSON processing pipeline with timing."""
    print("=" * 60)
    print("JSON Processing Pipeline")
    print("=" * 60)

    # Stage 1: Load JSON files
    print("\n[Stage 1] Loading JSON files...")
    start = time.perf_counter()
    records = load_json_files(data_dir)
    stage1_time = time.perf_counter() - start
    print(f"  Loaded {len(records)} files")
    total_records = sum(len(r) if isinstance(r, list) else 1 for r in records)
    print(f"  Total records: {total_records}")
    print(f"  Time: {stage1_time:.4f}s")

    # Flatten nested records
    flattened = []
    for item in records:
        if isinstance(item, list):
            flattened.extend(item)
        else:
            flattened.append(item)

    # Stage 2: Validate schema
    print("\n[Stage 2] Validating schema...")
    start = time.perf_counter()
    valid_records, invalid_count = validate_schema(flattened)
    stage2_time = time.perf_counter() - start
    print(f"  Valid records: {len(valid_records)}")
    print(f"  Invalid records: {invalid_count}")
    print(f"  Time: {stage2_time:.4f}s")

    # Stage 3: Merge and deduplicate
    print("\n[Stage 3] Merging and deduplicating...")
    start = time.perf_counter()
    unique_records = merge_records(valid_records)
    stage3_time = time.perf_counter() - start
    print(f"  Unique records: {len(unique_records)}")
    print(f"  Time: {stage3_time:.4f}s")

    # Summary
    total_time = stage1_time + stage2_time + stage3_time
    print("\n" + "=" * 60)
    print("TIMING SUMMARY")
    print("=" * 60)
    print(f"Stage 1 (Load):        {stage1_time:.4f}s ({100*stage1_time/total_time:5.1f}%)")
    print(f"Stage 2 (Validate):    {stage2_time:.4f}s ({100*stage2_time/total_time:5.1f}%)")
    print(f"Stage 3 (Merge):       {stage3_time:.4f}s ({100*stage3_time/total_time:5.1f}%)")
    print("─" * 60)
    print(f"Total:                 {total_time:.4f}s")


if __name__ == '__main__':
    run_pipeline()
