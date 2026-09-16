"""Main Log Processing Pipeline"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from log_pipeline.loader import LogLoader
from log_pipeline.parser import LogParser
from log_pipeline.enricher import LogEnricher
from log_pipeline.aggregator import LogAggregator
from log_pipeline.reporter import LogReporter


def run_log_pipeline():
    """Run the complete log processing pipeline."""
    start_time = time.time()

    print("=" * 70)
    print("Log Processing Pipeline")
    print("=" * 70)

    # Stage 1: Load log events
    print("\n[1/5] Loading log events...")
    t = time.time()
    loader = LogLoader(simulate_io=True)
    events = loader.load_events(n_events=80000)
    print(f"      Loaded {len(events)} events in {time.time()-t:.4f}s")

    # Stage 2: Parse and normalize
    print("\n[2/5] Parsing events...")
    t = time.time()
    parser = LogParser()
    parsed = parser.parse_events(events)
    print(f"      Parsed in {time.time()-t:.4f}s")

    # Stage 3: Enrich with metadata (BOTTLENECK in regressed version)
    print("\n[3/5] Enriching events with metadata...")
    t = time.time()
    enricher = LogEnricher()
    enriched = enricher.enrich_events(parsed)
    print(f"      Enriched {len(enriched)} events in {time.time()-t:.4f}s")

    # Stage 4: Aggregate
    print("\n[4/5] Aggregating by service and host...")
    t = time.time()
    aggregator = LogAggregator()
    service_summary = aggregator.aggregate_by_service(enriched)
    host_summary = aggregator.aggregate_by_host(enriched)
    print(f"      Aggregated in {time.time()-t:.4f}s")

    # Stage 5: Report
    print("\n[5/5] Formatting output...")
    t = time.time()
    reporter = LogReporter()
    service_report = reporter.format_service_summary(service_summary)
    host_report = reporter.format_host_summary(host_summary)
    print(f"      Formatted in {time.time()-t:.4f}s")

    elapsed = time.time() - start_time
    print(f"\n{'='*70}")
    print(f"Pipeline completed in {elapsed:.4f}s")
    print(f"{'='*70}\n")
    return elapsed


if __name__ == "__main__":
    run_log_pipeline()
