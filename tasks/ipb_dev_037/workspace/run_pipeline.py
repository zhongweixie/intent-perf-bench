"""Main Purchase Analytics Pipeline

Orchestrates the complete customer purchase analytics workflow.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from purchase_pipeline import (
    PurchaseLoader,
    PurchaseValidator,
    ProductEnricher,
    compute_customer_stats,
    segment_customers,
    build_report,
)


def run_pipeline():
    """Run the complete purchase analytics pipeline.

    Returns:
        Total elapsed time in seconds.
    """
    start = time.perf_counter()

    print("=" * 70)
    print("Customer Purchase Analytics Pipeline")
    print("=" * 70)

    # Stage 1: Load purchase records
    print("\n[1/6] Loading purchase records...")
    t = time.perf_counter()
    loader = PurchaseLoader(simulate_io=True)
    df = loader.load_purchases(n_records=100000)
    print(f"      Loaded {len(df):,} records in {time.perf_counter() - t:.4f}s")

    # Stage 2: Validate records
    print("\n[2/6] Validating records...")
    t = time.perf_counter()
    validator = PurchaseValidator()
    df = validator.validate(df)
    print(f"      Validated in {time.perf_counter() - t:.4f}s")

    # Stage 3: Enrich with product catalog
    print("\n[3/6] Enriching with product catalog...")
    t = time.perf_counter()
    enricher = ProductEnricher()
    df = enricher.enrich(df)
    print(f"      Enriched in {time.perf_counter() - t:.4f}s")

    # Stage 4: Compute customer statistics
    print("\n[4/6] Computing customer statistics...")
    t = time.perf_counter()
    customer_stats = compute_customer_stats(df)
    print(f"      Computed stats for {len(customer_stats):,} customers in {time.perf_counter() - t:.4f}s")

    # Stage 5: Segment customers
    print("\n[5/6] Segmenting customers...")
    t = time.perf_counter()
    segments = segment_customers(customer_stats)
    print(f"      Segmented in {time.perf_counter() - t:.4f}s")

    # Stage 6: Build report
    print("\n[6/6] Building report...")
    t = time.perf_counter()
    report = build_report(customer_stats, segments)
    print(f"      Report built in {time.perf_counter() - t:.4f}s")

    elapsed = time.perf_counter() - start
    print(f"\n{'=' * 70}")
    print(f"Pipeline completed in {elapsed:.4f}s")
    print(f"{'=' * 70}\n")
    return elapsed


if __name__ == "__main__":
    run_pipeline()
