"""Main Order Processing Pipeline"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from order_pipeline.loader import OrderLoader
from order_pipeline.expander import OrderExpander
from order_pipeline.aggregator import OrderAggregator
from order_pipeline.validator import OrderValidator
from order_pipeline.formatter import ReportFormatter


def run_order_pipeline():
    """Run the complete order processing pipeline."""
    start_time = time.time()

    print("=" * 70)
    print("Order Processing Pipeline")
    print("=" * 70)

    # Stage 1: Load orders
    print("\n[1/5] Loading orders...")
    t = time.time()
    loader = OrderLoader(simulate_io=True)
    orders = loader.load_orders(n_orders=30000)
    print(f"      Loaded {len(orders)} orders in {time.time()-t:.4f}s")

    # Stage 2: Validate
    print("\n[2/5] Validating orders...")
    t = time.time()
    validator = OrderValidator()
    valid = validator.validate_orders(orders)
    print(f"      Validation {'passed' if valid else 'failed'} in {time.time()-t:.4f}s")

    # Stage 3: Expand line items (BOTTLENECK in regressed version)
    print("\n[3/5] Expanding order items...")
    t = time.time()
    expander = OrderExpander()
    detail = expander.expand_order_items(orders)
    print(f"      Expanded to {len(detail)} detail rows in {time.time()-t:.4f}s")

    # Stage 4: Aggregate
    print("\n[4/5] Aggregating reports...")
    t = time.time()
    aggregator = OrderAggregator()
    region_summary = aggregator.aggregate_by_region_item(detail)
    customer_summary = aggregator.aggregate_by_customer(detail)
    print(f"      Aggregated in {time.time()-t:.4f}s")

    # Stage 5: Format
    print("\n[5/5] Formatting output...")
    t = time.time()
    formatter = ReportFormatter()
    region_report = formatter.format_region_summary(region_summary)
    customer_report = formatter.format_customer_summary(customer_summary)
    print(f"      Formatted in {time.time()-t:.4f}s")

    elapsed = time.time() - start_time
    print(f"\n{'='*70}")
    print(f"Pipeline completed in {elapsed:.4f}s")
    print(f"{'='*70}\n")
    return elapsed


if __name__ == "__main__":
    run_order_pipeline()
