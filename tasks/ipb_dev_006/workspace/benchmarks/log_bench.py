"""Benchmark for log pipeline — verifies the performance regression is fixed."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from log_pipeline.loader import LogLoader
from log_pipeline.parser import LogParser
from log_pipeline.enricher import LogEnricher
from log_pipeline.aggregator import LogAggregator
from log_pipeline.reporter import LogReporter

THRESHOLD = 0.28  # baseline ~0.07-0.21s (no I/O), regressed ~0.40s (no I/O)


def run_once():
    loader = LogLoader(simulate_io=False)
    events = loader.load_events(n_events=80000)
    parser = LogParser()
    parsed = parser.parse_events(events)
    enricher = LogEnricher()
    enriched = enricher.enrich_events(parsed)
    aggregator = LogAggregator()
    service_summary = aggregator.aggregate_by_service(enriched)
    host_summary = aggregator.aggregate_by_host(enriched)
    reporter = LogReporter()
    reporter.format_service_summary(service_summary)
    reporter.format_host_summary(host_summary)


def benchmark():
    print(f"Running log pipeline benchmark (threshold: {THRESHOLD}s, no I/O)...")
    times = []
    for i in range(5):
        t = time.time()
        run_once()
        elapsed = time.time() - t
        times.append(elapsed)
        print(f"  run {i+1}: {elapsed:.4f}s")

    best = min(times)
    print(f"\nBest time: {best:.4f}s  (threshold: {THRESHOLD}s)")
    if best <= THRESHOLD:
        print("PASS: pipeline meets performance threshold")
        return True
    else:
        print(f"FAIL: pipeline too slow ({best:.4f}s > {THRESHOLD}s)")
        return False


if __name__ == "__main__":
    passed = benchmark()
    sys.exit(0 if passed else 1)
