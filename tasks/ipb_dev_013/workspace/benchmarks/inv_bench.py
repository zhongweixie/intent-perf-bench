"""Benchmark for inventory pipeline."""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from inventory.loader import InventoryLoader
from inventory.reorder_checker import ReorderChecker
from inventory.aggregator import InventoryAggregator

THRESHOLD = 0.08

def run_once():
    loader = InventoryLoader(simulate_io=False)
    inv = loader.load_inventory(n=30000)
    checker = ReorderChecker()
    scored = checker.compute_reorder_status(inv)
    agg = InventoryAggregator()
    return agg.aggregate_by_warehouse(scored)

def benchmark():
    print(f"Inventory Pipeline Benchmark (threshold: {THRESHOLD}s)")
    times = []
    for i in range(5):
        t = time.time(); run_once(); e = time.time()-t
        times.append(e); print(f"  run {i+1}: {e:.4f}s")
    best = min(times)
    print(f"\nBest: {best:.4f}s  threshold: {THRESHOLD}s")
    if best <= THRESHOLD:
        print("PASS: pipeline meets performance threshold"); return True
    print(f"FAIL: too slow ({best:.4f}s > {THRESHOLD}s)"); return False

if __name__ == "__main__":
    import sys; sys.exit(0 if benchmark() else 1)
