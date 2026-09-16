"""Churn Prediction Benchmark"""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from churn.loader import CustomerLoader
from churn.predictor import ChurnPredictor
from churn.aggregator import ChurnAggregator

THRESHOLD = 0.12

def run_once():
    loader = CustomerLoader(simulate_io=False)
    customers = loader.load_customers(n=25000)
    predictor = ChurnPredictor()
    scored = predictor.predict_churn(customers)
    agg = ChurnAggregator()
    return agg.aggregate_by_contract(scored)

def benchmark():
    print(f"Churn Prediction Benchmark (threshold: {THRESHOLD}s)")
    times = []; 
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
