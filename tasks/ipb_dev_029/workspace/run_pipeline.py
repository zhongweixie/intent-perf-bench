#!/usr/bin/env python3
"""Run JSON processing pipeline with timing."""

import time
from json_processor import parse_json_stream, extract_nested_values


def run_pipeline():
    """Run JSON processing pipeline with timing."""
    print("=" * 60)
    print("JSON Processing Pipeline")
    print("=" * 60)

    # Stage 1: Load JSON lines
    print("\n[Stage 1] Loading JSON lines...")
    start = time.perf_counter()
    with open('test_data.jsonl', 'r', encoding='utf-8') as f:
        json_lines = [line.strip() for line in f if line.strip()]
    stage1_time = time.perf_counter() - start
    print(f"  Loaded {len(json_lines)} JSON lines")
    print(f"  Time: {stage1_time:.4f}s")

    # Stage 2: Parse JSON
    print("\n[Stage 2] Parsing JSON...")
    start = time.perf_counter()
    objects = parse_json_stream(json_lines)
    stage2_time = time.perf_counter() - start
    print(f"  Parsed {len(objects)} objects")
    print(f"  Time: {stage2_time:.4f}s")

    # Stage 3: Extract nested values
    print("\n[Stage 3] Extracting nested values...")
    start = time.perf_counter()
    names = extract_nested_values(objects, 'user.profile.name')
    emails = extract_nested_values(objects, 'user.profile.email')
    cpu_metrics = extract_nested_values(objects, 'data.metrics.cpu')
    stage3_time = time.perf_counter() - start
    print(f"  Extracted {len(names)} names")
    print(f"  Extracted {len(emails)} emails")
    print(f"  Extracted {len(cpu_metrics)} CPU metrics")
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
