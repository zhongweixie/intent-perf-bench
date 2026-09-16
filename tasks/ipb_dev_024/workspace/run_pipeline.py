#!/usr/bin/env python3
"""Run JSON processing pipeline with timing."""

import time
from json_processor import parse_records, extract_fields


def run_pipeline():
    """Run JSON processing pipeline with timing."""
    print("=" * 60)
    print("JSON Processing Pipeline")
    print("=" * 60)

    # Stage 1: Load data
    print("\n[Stage 1] Loading test data...")
    start = time.perf_counter()
    with open('test_data.json', 'r', encoding='utf-8') as f:
        json_string = f.read()
    stage1_time = time.perf_counter() - start
    print(f"  Loaded {len(json_string) / 1024 / 1024:.2f} MB")
    print(f"  Time: {stage1_time:.4f}s")

    # Stage 2: Parse JSON
    print("\n[Stage 2] Parsing JSON...")
    start = time.perf_counter()
    records = parse_records(json_string)
    stage2_time = time.perf_counter() - start
    print(f"  Parsed {len(records)} records")
    print(f"  Time: {stage2_time:.4f}s")

    # Stage 3: Extract fields
    print("\n[Stage 3] Extracting fields...")
    start = time.perf_counter()
    field_names = ['id', 'timestamp', 'value', 'status']
    extracted = extract_fields(records, field_names)
    stage3_time = time.perf_counter() - start
    print(f"  Extracted {len(field_names)} fields from {len(extracted)} records")
    print(f"  Time: {stage3_time:.4f}s")

    # Summary
    total_time = stage1_time + stage2_time + stage3_time
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Stage 1 (Load):    {stage1_time:.4f}s")
    print(f"  Stage 2 (Parse):   {stage2_time:.4f}s")
    print(f"  Stage 3 (Extract): {stage3_time:.4f}s")
    print(f"  Total:             {total_time:.4f}s")
    print("=" * 60)


if __name__ == '__main__':
    run_pipeline()
