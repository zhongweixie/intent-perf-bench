"""Main Event Analytics Pipeline

Eight-stage pipeline. Per-stage timing is intentionally omitted;
use the benchmark script to measure overall throughput.
"""
import sys
import time
import json
import pathlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
import pandas as pd

from event_pipeline.ingester import EventIngester
from event_pipeline.normalizer import EventNormalizer
from event_pipeline.enricher import EventEnricher
from event_pipeline.scorer import AnomalyScorer
from event_pipeline.batch_runner import BatchRunner
from event_pipeline.classifier import classify_events
from event_pipeline.aggregator import EventAggregator
from event_pipeline.reporter import ReportBuilder


def _build_historical(n: int = 500000) -> pd.DataFrame:
    np.random.seed(0)
    return pd.DataFrame({
        'segment': np.random.choice([f's{i}' for i in range(20)], n),
        'value':   np.random.exponential(50.0, n),
    })


def run_pipeline():
    start = time.perf_counter()
    print("=" * 70)
    print("Event Analytics Pipeline")
    print("=" * 70)

    print("\nIngesting events...")
    ingester = EventIngester(simulate_io=True)
    df = ingester.ingest(n_records=100000)
    print(f"  Loaded {len(df):,} events")

    print("Normalizing events...")
    normalizer = EventNormalizer()
    df = normalizer.normalize(df)

    print("Enriching with catalog...")
    enricher = EventEnricher()
    df = enricher.enrich(df)

    print("Initialising anomaly scorer...")
    historical = _build_historical()
    scorer = AnomalyScorer(historical)

    print("Running anomaly scoring in batches...")
    runner = BatchRunner(scorer)
    scores = runner.run(df)
    print(f"  Scored {len(scores):,} events")

    print("Classifying anomaly tiers...")
    tiers = classify_events(scores)

    print("Aggregating results...")
    aggregator = EventAggregator()
    aggregation = aggregator.aggregate(df, tiers)

    print("Building report...")
    report = ReportBuilder().build(aggregation, scores)

    elapsed = time.perf_counter() - start
    print(f"\n{'=' * 70}")
    print(f"Pipeline completed in {elapsed:.4f}s")
    print(f"Total events  : {report['total_events']:,}")
    print(f"Critical      : {report['critical_events']:,}")
    print(f"{'=' * 70}\n")
    return elapsed


if __name__ == "__main__":
    run_pipeline()
