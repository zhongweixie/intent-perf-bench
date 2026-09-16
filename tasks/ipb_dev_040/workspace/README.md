# Event Analytics Pipeline

## Overview
Eight-stage pipeline that ingests events, normalizes them, and detects
anomalies against historical segment benchmarks.

## Stages
1. **Ingest** — load raw events
2. **Normalize** — parse dates, extract tags, filter, label
3. **Enrich** — join event catalog
4. **Score** — anomaly scorer with historical benchmarks
5. **Batch-run** — scorer in batches
6. **Classify** — anomaly tier assignment
7. **Aggregate** — count by tier and source
8. **Report** — summary

## Running
```bash
python3 run_pipeline.py
python3 benchmarks/event_bench.py
```

## Benchmark Threshold
Passes when `best_time <= 0.55s`.
