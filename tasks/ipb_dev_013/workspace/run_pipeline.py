"""Inventory Management Pipeline"""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from inventory.loader import InventoryLoader
from inventory.reorder_checker import ReorderChecker
from inventory.aggregator import InventoryAggregator

def run_inventory_pipeline():
    print("=" * 60)
    print("Inventory Management Pipeline")
    print("=" * 60)
    t = time.time()
    loader = InventoryLoader(simulate_io=True)
    inv = loader.load_inventory(n=30000)
    print(f"\n[1/3] Load:      {time.time()-t:.4f}s  ({len(inv)} SKUs)")
    t = time.time()
    checker = ReorderChecker()
    scored = checker.compute_reorder_status(inv)
    print(f"[2/3] Check:     {time.time()-t:.4f}s")
    t = time.time()
    agg = InventoryAggregator()
    summary = agg.aggregate_by_warehouse(scored)
    print(f"[3/3] Aggregate: {time.time()-t:.4f}s")
    return summary

if __name__ == "__main__":
    run_inventory_pipeline()
