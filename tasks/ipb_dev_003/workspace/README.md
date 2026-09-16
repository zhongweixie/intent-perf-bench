# ETL Pipeline Project

A high-performance data processing pipeline for transaction analysis.

## Quick Start

```bash
# Generate sample data
python3 generate_data.py

# Run the pipeline
python3 run_pipeline.py

# Run benchmark
python3 benchmarks/pipeline_bench.py
```

## Performance Requirements

The pipeline must process 100k transactions in under **1.5 seconds** (see `.github/workflows/performance.yml`).

## Project Structure

- `pipeline/` - Core ETL modules
- `data/` - Transaction data
- `benchmarks/` - Performance tests
- `output/` - Processed results
