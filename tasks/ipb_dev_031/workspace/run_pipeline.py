#!/usr/bin/env python3
"""Run log analysis pipeline with timing."""

import time
from log_analyzer import parse_log_lines, count_error_types


def run_pipeline():
    print("=" * 60)
    print("Log Analysis Pipeline")
    print("=" * 60)

    print("\n[Stage 1] Loading log lines...")
    start = time.perf_counter()
    with open('test_logs.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    stage1_time = time.perf_counter() - start
    print(f"  Loaded {len(lines)} lines")
    print(f"  Time: {stage1_time:.4f}s")

    print("\n[Stage 2] Parsing log entries...")
    start = time.perf_counter()
    log_entries = parse_log_lines(lines)
    stage2_time = time.perf_counter() - start
    print(f"  Parsed {len(log_entries)} entries")
    print(f"  Time: {stage2_time:.4f}s")

    print("\n[Stage 3] Counting by level...")
    start = time.perf_counter()
    counts = count_error_types(log_entries)
    stage3_time = time.perf_counter() - start
    print(f"  Level counts: {counts}")
    print(f"  Time: {stage3_time:.4f}s")

    total_time = stage1_time + stage2_time + stage3_time
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Stage 1 (Load):   {stage1_time:.4f}s")
    print(f"  Stage 2 (Parse):  {stage2_time:.4f}s")
    print(f"  Stage 3 (Count):  {stage3_time:.4f}s")
    print(f"  Total:            {total_time:.4f}s")


if __name__ == '__main__':
    run_pipeline()
