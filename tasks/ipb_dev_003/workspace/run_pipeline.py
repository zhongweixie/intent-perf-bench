"""ETL Pipeline Main Script"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from pipeline import (
    DataLoader,
    DataValidator,
    DataTransformer,
    DataAggregator,
    DataEnricher,
    DataExporter,
    PerformanceMonitor,
)


def run_pipeline():
    """Execute the full ETL pipeline."""
    monitor = PerformanceMonitor()

    print("Starting ETL Pipeline...")
    pipeline_start = time.time()

    # Stage 1: Load data
    with monitor.measure("1_load"):
        loader = DataLoader(data_dir="data")
        transactions = loader.load_transactions()
        print(f"Loaded {len(transactions)} transactions")

    # Stage 2: Validate
    with monitor.measure("2_validate"):
        validator = DataValidator()
        transactions = validator.validate(transactions)
        transactions = validator.check_duplicates(transactions)

    # Stage 3: Transform (THIS IS THE PERFORMANCE-CRITICAL STAGE!)
    with monitor.measure("3_transform"):
        transformer = DataTransformer(window_hours=24)
        transactions = transformer.add_time_features(transactions)
        transactions = transformer.calculate_metrics(transactions)
        print(f"Transformed to {len(transactions)} records with window metrics")

    # Stage 4: Aggregate
    with monitor.measure("4_aggregate"):
        aggregator = DataAggregator()
        customer_metrics = aggregator.aggregate_by_customer(transactions)
        time_metrics = aggregator.aggregate_by_time_period(transactions, freq='D')

    # Stage 5: Enrich
    with monitor.measure("5_enrich"):
        enricher = DataEnricher()
        clv = enricher.calculate_customer_lifetime_value(transactions)

    # Stage 6: Export
    with monitor.measure("6_export"):
        exporter = DataExporter(output_dir="output")
        exporter.export_to_parquet(transactions, "transactions_processed.parquet")
        exporter.export_to_csv(customer_metrics, "customer_metrics.csv")
        exporter.export_summary_stats(transactions)

    pipeline_end = time.time()
    total_time = pipeline_end - pipeline_start

    print(f"\n✓ Pipeline completed in {total_time:.4f}s")

    monitor.print_report()

    return total_time


if __name__ == "__main__":
    run_pipeline()
