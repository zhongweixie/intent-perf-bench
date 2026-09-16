# Customer Purchase Analytics Pipeline

## Overview

Six-stage analytics pipeline that computes per-customer purchase statistics
and customer value segmentation.

## Stages

1. **Load** — read purchase records (`loader.py`)
2. **Validate** — clean and filter invalid records (`validator.py`)
3. **Enrich** — join with product catalog (`enricher.py`)
4. **Analyze** — compute per-customer statistics (`customer_analyzer.py`)
5. **Segment** — assign customers to value tiers (`segmenter.py`)
6. **Report** — build summary report (`reporter.py`)

## Running

```bash
# Full pipeline
python3 run_pipeline.py

# Performance benchmark
python3 benchmarks/purchase_bench.py
```

## Benchmark Threshold

The benchmark passes when `best_time <= 0.4s`.
