# Customer Scoring Pipeline

## Overview

Eight-stage pipeline that scores customers by comparing their transaction
values against historical segment benchmarks.

## Stages

1. **Load** — read customer transaction records (`loader.py`)
2. **Validate** — clean invalid rows (`validator.py`)
3. **Parse dates** — convert purchase_date strings (`date_parser.py`)
4. **Enrich** — join product catalog (`enricher.py`)
5. **Score** — z-score vs segment benchmarks (`scorer.py`)
6. **Batch-process** — run scorer in batches (`batch_processor.py`)
7. **Segment** — classify anomaly tier (`segmenter.py`)
8. **Report** — build summary (`reporter.py`)

## Running

```bash
python3 run_pipeline.py
python3 benchmarks/customer_bench.py
```

## Benchmark Threshold

Passes when `best_time <= 0.4s`.
