"""Profile inventory pipeline to identify bottlenecks."""
import sys, time, cProfile, pstats, io
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from inventory.loader import InventoryLoader
from inventory.reorder_checker import ReorderChecker
from inventory.aggregator import InventoryAggregator

def run_once():
    loader = InventoryLoader(simulate_io=False)
    inv = loader.load_inventory(n=30000)
    checker = ReorderChecker()
    scored = checker.compute_reorder_status(inv)
    agg = InventoryAggregator()
    return agg.aggregate_by_warehouse(scored)

# Profile the execution
pr = cProfile.Profile()
pr.enable()
result = run_once()
pr.disable()

# Print stats
s = io.StringIO()
ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
ps.print_stats(15)
print(s.getvalue())
