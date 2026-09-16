#!/usr/bin/env python3
"""Run event processing pipeline with timing."""

import json
import time
from event_processor import process_events, aggregate_by_type


def run_pipeline():
    print("=" * 60)
    print("Event Processing Pipeline")
    print("=" * 60)

    print("\n[Stage 1] Loading events...")
    start = time.perf_counter()
    with open('test_events.json', 'r', encoding='utf-8') as f:
        events = json.load(f)
    stage1_time = time.perf_counter() - start
    print(f"  Loaded {len(events)} events")
    print(f"  Time: {stage1_time:.4f}s")

    print("\n[Stage 2] Processing events...")
    start = time.perf_counter()
    processed = process_events(events)
    stage2_time = time.perf_counter() - start
    print(f"  Processed {len(processed)} events")
    print(f"  Time: {stage2_time:.4f}s")

    print("\n[Stage 3] Aggregating by type...")
    start = time.perf_counter()
    stats = aggregate_by_type(processed)
    stage3_time = time.perf_counter() - start
    print(f"  {len(stats)} event types")
    print(f"  Time: {stage3_time:.4f}s")

    total_time = stage1_time + stage2_time + stage3_time
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Stage 1 (Load):      {stage1_time:.4f}s")
    print(f"  Stage 2 (Process):   {stage2_time:.4f}s")
    print(f"  Stage 3 (Aggregate): {stage3_time:.4f}s")
    print(f"  Total:               {total_time:.4f}s")


if __name__ == '__main__':
    run_pipeline()
