#!/usr/bin/env python3
"""Interactive pipeline runner for order analytics."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time
from order_analytics import load_orders, build_user_report


def main():
    print("Stage 1 — Loading orders...")
    t0 = time.perf_counter()
    orders = load_orders()
    t_load = time.perf_counter() - t0
    print(f"  Loaded {len(orders)} orders in {t_load:.3f}s")

    print("Stage 2 — Building user report...")
    t0 = time.perf_counter()
    report = build_user_report(orders)
    t_report = time.perf_counter() - t0
    print(f"  Built report for {len(report)} users in {t_report:.3f}s")

    total_revenue = report['revenue'].sum()
    avg_return    = report['return_rate'].mean()
    print(f"  Total revenue:  ${total_revenue:,.2f}")
    print(f"  Avg return rate: {avg_return:.1%}")
    print(f"\nTotal pipeline time: {t_load + t_report:.3f}s")


if __name__ == '__main__':
    main()
