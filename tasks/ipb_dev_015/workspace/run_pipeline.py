"""Log Aggregation Pipeline Runner"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from log_aggregator.loader import LogLoader
from log_aggregator.aggregator import LogAggregator
from log_aggregator.reporter import LogReporter


def run_aggregation_pipeline():
    """Run the complete log aggregation pipeline."""
    t_total = time.time()
    print("=" * 70)
    print("Log Aggregation Pipeline")
    print("=" * 70)

    # Stage 1: Load logs
    print("\n[1/3] Loading logs...")
    t = time.time()
    loader = LogLoader(simulate_io=True)
    logs = loader.load_logs(n_logs=30000)
    stage1_time = time.time() - t
    print(f"      Loaded {len(logs)} logs in {stage1_time:.4f}s")

    # Stage 2: Aggregate by window
    print("\n[2/3] Aggregating by time window...")
    t = time.time()
    aggregator = LogAggregator()
    aggregated = aggregator.aggregate_by_window(logs, window='1min')
    stage2_time = time.time() - t
    print(f"      Aggregated into {len(aggregated)} windows in {stage2_time:.4f}s")

    # Stage 3: Generate report
    print("\n[3/3] Generating report...")
    t = time.time()
    reporter = LogReporter()
    report = reporter.generate_report(aggregated)
    stage3_time = time.time() - t
    print(f"      Report generated in {stage3_time:.4f}s")

    elapsed = time.time() - t_total
    print(f"\nPipeline completed in {elapsed:.4f}s")
    print(f"  Load:      {stage1_time:.4f}s")
    print(f"  Aggregate: {stage2_time:.4f}s")
    print(f"  Report:    {stage3_time:.4f}s")
    return elapsed


if __name__ == "__main__":
    run_aggregation_pipeline()
