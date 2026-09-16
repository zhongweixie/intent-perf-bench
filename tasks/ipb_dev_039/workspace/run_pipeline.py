"""Main Customer Scoring Pipeline

Eight-stage pipeline. Per-stage timing is omitted; use the benchmark for
overall throughput measurement.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from customer_pipeline.loader import CustomerLoader
from customer_pipeline.validator import DataValidator
from customer_pipeline.date_parser import DateParser
from customer_pipeline.enricher import CatalogEnricher
from customer_pipeline.scorer import CustomerScorer
from customer_pipeline.batch_processor import BatchProcessor
from customer_pipeline.segmenter import segment_by_score
from customer_pipeline.reporter import ReportBuilder

import numpy as np
import pandas as pd


def _build_historical(n: int = 200000) -> pd.DataFrame:
    """Build historical reference dataset for the scorer."""
    np.random.seed(0)
    return pd.DataFrame({
        'segment': np.random.choice([f's{i}' for i in range(10)], n),
        'value':   np.random.exponential(50.0, n),
    })


def run_pipeline():
    start = time.perf_counter()
    print("=" * 70)
    print("Customer Scoring Pipeline")
    print("=" * 70)

    print("\nLoading customer records...")
    loader = CustomerLoader(simulate_io=True)
    df = loader.load(n_records=100000)
    print(f"  Loaded {len(df):,} records")

    print("Validating data...")
    df = DataValidator().validate(df)

    print("Parsing dates...")
    df = DateParser().parse(df)

    print("Enriching with product catalog...")
    df = CatalogEnricher().enrich(df)

    print("Initialising scorer with historical data...")
    historical = _build_historical()
    scorer = CustomerScorer(historical)

    print("Scoring customers in batches...")
    processor = BatchProcessor(scorer)
    scores = processor.process(df)
    print(f"  Scored {len(scores):,} records")

    print("Classifying anomaly tiers...")
    tiers = segment_by_score(scores)

    print("Building report...")
    report = ReportBuilder().build(scores, tiers)

    elapsed = time.perf_counter() - start
    print(f"\n{'=' * 70}")
    print(f"Pipeline completed in {elapsed:.4f}s")
    print(f"Total records   : {report['total_records']:,}")
    print(f"High anomalies  : {report['high_anomalies']:,}")
    print(f"Alerts          : {report['high_anomalies']}")
    print(f"{'=' * 70}\n")
    return elapsed


if __name__ == "__main__":
    run_pipeline()
