"""Main Analytics Pipeline

Orchestrates the complete data analytics workflow.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from analytics.loader import DataLoader
from analytics.aggregator import MetricsAggregator
from analytics.validator import DataValidator
from analytics.filters import DataFilter
from analytics.reporter import ReportGenerator
import time


def run_analytics_pipeline():
    """
    Run the complete analytics pipeline.

    Returns:
        Total elapsed time in seconds
    """
    start_time = time.time()

    print("="*70)
    print("Data Analytics Pipeline")
    print("="*70)

    # Stage 1: Load data
    print("\n[1/5] Loading data...")
    stage_start = time.time()
    loader = DataLoader(simulate_io=True)
    df = loader.load_transactions(n_records=50000)
    stage_time = time.time() - stage_start
    print(f"      Loaded {len(df)} records in {stage_time:.4f}s")

    # Stage 2: Validate data
    print("\n[2/5] Validating data...")
    stage_start = time.time()
    validator = DataValidator()
    is_valid = validator.validate_data(df)
    stage_time = time.time() - stage_start
    print(f"      Validation {'passed' if is_valid else 'failed'} in {stage_time:.4f}s")

    # Stage 3: Calculate metrics (BOTTLENECK)
    print("\n[3/5] Calculating metrics...")
    stage_start = time.time()
    aggregator = MetricsAggregator()
    df_with_metrics = aggregator.calculate_derived_metrics(df)
    stage_time = time.time() - stage_start
    print(f"      Computed metrics in {stage_time:.4f}s")

    # Stage 4: Aggregate results
    print("\n[4/5] Aggregating results...")
    stage_start = time.time()
    customer_agg = aggregator.aggregate_by_customer(df_with_metrics)
    region_agg = aggregator.aggregate_by_region(df_with_metrics)
    stage_time = time.time() - stage_start
    print(f"      Aggregated data in {stage_time:.4f}s")

    # Stage 5: Generate reports
    print("\n[5/5] Generating reports...")
    stage_start = time.time()
    reporter = ReportGenerator()
    customer_report = reporter.generate_customer_report(customer_agg)
    region_report = reporter.generate_region_report(region_agg)
    stage_time = time.time() - stage_start
    print(f"      Generated reports in {stage_time:.4f}s")

    elapsed = time.time() - start_time
    print(f"\n{'='*70}")
    print(f"Pipeline completed in {elapsed:.4f}s")
    print(f"{'='*70}\n")

    return elapsed


if __name__ == "__main__":
    elapsed = run_analytics_pipeline()
    sys.exit(0)
