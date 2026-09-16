#!/usr/bin/env python3
"""Run text processing pipeline with timing."""

import json
import time
from text_processor import count_patterns, extract_keywords


def run_pipeline():
    """Run text processing pipeline with timing."""
    print("=" * 60)
    print("Text Processing Pipeline")
    print("=" * 60)

    # Stage 1: Load data
    print("\n[Stage 1] Loading text data...")
    start = time.perf_counter()
    with open('text_data.json', 'r', encoding='utf-8') as f:
        texts = json.load(f)
    stage1_time = time.perf_counter() - start
    print(f"  Loaded {len(texts)} text entries")
    print(f"  Time: {stage1_time:.4f}s")

    # Stage 2: Count patterns
    print("\n[Stage 2] Counting patterns...")
    patterns = ['system', 'error', 'failed', 'success', 'processing']
    start = time.perf_counter()
    pattern_counts = count_patterns(texts, patterns)
    stage2_time = time.perf_counter() - start
    print(f"  Pattern counts: {pattern_counts}")
    print(f"  Time: {stage2_time:.4f}s")

    # Stage 3: Extract keywords
    print("\n[Stage 3] Extracting keywords...")
    start = time.perf_counter()
    keywords = extract_keywords(texts, min_length=4)
    stage3_time = time.perf_counter() - start
    top_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:10]
    print(f"  Top keywords: {dict(top_keywords)}")
    print(f"  Time: {stage3_time:.4f}s")

    # Summary
    total_time = stage1_time + stage2_time + stage3_time
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Stage 1 (Load):     {stage1_time:.4f}s")
    print(f"  Stage 2 (Patterns): {stage2_time:.4f}s")
    print(f"  Stage 3 (Keywords): {stage3_time:.4f}s")
    print(f"  Total:              {total_time:.4f}s")
    print("=" * 60)


if __name__ == '__main__':
    run_pipeline()
