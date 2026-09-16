#!/usr/bin/env python3
"""Interactive pipeline runner for pricing engine."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time
from pricing_engine import load_orders, calculate_order_totals


def main():
    print("Loading orders...")
    t0 = time.perf_counter()
    orders = load_orders()
    t_load = time.perf_counter() - t0
    print(f"  Loaded {len(orders)} orders in {t_load:.4f}s")

    print("Calculating order totals...")
    t0 = time.perf_counter()
    results = calculate_order_totals(orders)
    t_calc = time.perf_counter() - t0
    print(f"  Calculated {len(results)} totals in {t_calc:.4f}s")

    total_revenue = sum(results)
    print(f"  Total revenue: ${total_revenue:,.2f}")
    print(f"\nTotal pipeline time: {t_load + t_calc:.4f}s")


if __name__ == '__main__':
    main()
