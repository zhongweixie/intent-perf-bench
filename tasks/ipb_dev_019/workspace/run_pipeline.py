#!/usr/bin/env python3
"""Query engine pipeline runner."""

import json
import time
from query_engine import build_index, apply_filters, search_records


def run_pipeline(data_file='records.json'):
    """Run query engine pipeline with timing."""
    print("=" * 60)
    print("Query Engine Pipeline")
    print("=" * 60)

    # Stage 1: Load records
    print("\n[Stage 1] Loading records...")
    start = time.perf_counter()
    with open(data_file, 'r', encoding='utf-8') as f:
        records = json.load(f)
    stage1_time = time.perf_counter() - start
    print(f"  Loaded {len(records)} records")
    print(f"  Time: {stage1_time:.4f}s")

    # Stage 2: Build index
    print("\n[Stage 2] Building indexes...")
    start = time.perf_counter()
    index = build_index(records)
    stage2_time = time.perf_counter() - start
    print(f"  Indexed by: id, category, status")
    print(f"  Time: {stage2_time:.4f}s")

    # Stage 3: Run queries
    print("\n[Stage 3] Running queries...")
    start = time.perf_counter()

    # Query 1: Filter by category
    result1 = apply_filters(index, {'category': 'Electronics'})

    # Query 2: Filter by status
    result2 = apply_filters(index, {'status': 'active'})

    # Query 3: Combined filters
    result3 = apply_filters(index, {'category': 'Books', 'status': 'pending'})

    # Query 4: Text search
    result4 = search_records(records, ['Product', '00042'])

    stage3_time = time.perf_counter() - start
    print(f"  Query 1 (category='Electronics'): {len(result1)} results")
    print(f"  Query 2 (status='active'): {len(result2)} results")
    print(f"  Query 3 (category='Books' AND status='pending'): {len(result3)} results")
    print(f"  Query 4 (search=['Product', '00042']): {len(result4)} results")
    print(f"  Time: {stage3_time:.4f}s")

    # Summary
    total_time = stage1_time + stage2_time + stage3_time
    print("\n" + "=" * 60)
    print("TIMING SUMMARY")
    print("=" * 60)
    print(f"Stage 1 (Load):        {stage1_time:.4f}s ({100*stage1_time/total_time:5.1f}%)")
    print(f"Stage 2 (Index):       {stage2_time:.4f}s ({100*stage2_time/total_time:5.1f}%)")
    print(f"Stage 3 (Query):       {stage3_time:.4f}s ({100*stage3_time/total_time:5.1f}%)")
    print("─" * 60)
    print(f"Total:                 {total_time:.4f}s")


if __name__ == '__main__':
    run_pipeline()
