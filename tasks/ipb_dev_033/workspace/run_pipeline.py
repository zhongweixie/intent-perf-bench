#!/usr/bin/env python3
"""Run sorting pipeline with timing."""

import json
import time
from sorter import sort_records, find_top_k


def run_pipeline():
    print("=" * 60)
    print("Sorting Pipeline")
    print("=" * 60)

    print("\n[Stage 1] Loading records...")
    start = time.perf_counter()
    with open('test_records.json', 'r', encoding='utf-8') as f:
        records = json.load(f)
    stage1_time = time.perf_counter() - start
    print(f"  Loaded {len(records)} records")
    print(f"  Time: {stage1_time:.4f}s")

    print("\n[Stage 2] Sorting all records...")
    start = time.perf_counter()
    sorted_recs = sort_records(records, 'score')
    stage2_time = time.perf_counter() - start
    print(f"  Sorted {len(sorted_recs)} records")
    print(f"  Time: {stage2_time:.4f}s")

    print("\n[Stage 3] Finding top-10...")
    start = time.perf_counter()
    top_k = find_top_k(records, 'score', k=10)
    stage3_time = time.perf_counter() - start
    print(f"  Top score: {top_k[0]['score']}")
    print(f"  Time: {stage3_time:.4f}s")

    total_time = stage1_time + stage2_time + stage3_time
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Stage 1 (Load):  {stage1_time:.4f}s")
    print(f"  Stage 2 (Sort):  {stage2_time:.4f}s")
    print(f"  Stage 3 (Top-K): {stage3_time:.4f}s")
    print(f"  Total:           {total_time:.4f}s")


if __name__ == '__main__':
    run_pipeline()
