# Log Processing Pipeline

A log event enrichment pipeline that processes raw log events, enriches them
with reference metadata, and produces service/host summary reports.

## Pipeline Stages

1. **Load** — fetch raw log events (simulates I/O latency)
2. **Parse** — normalize host names, classify latency buckets
3. **Enrich** — join events with category reference metadata
4. **Aggregate** — group by service and host
5. **Report** — format summaries

## Running

```bash
python3 run_pipeline.py
```

## Benchmark

```bash
python3 benchmarks/log_bench.py
```

## Modules

- `log_pipeline/loader.py` — event loading
- `log_pipeline/parser.py` — normalization
- `log_pipeline/enricher.py` — metadata enrichment
- `log_pipeline/aggregator.py` — aggregation
- `log_pipeline/reporter.py` — formatting
