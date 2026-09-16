"""Benchmark for payment risk pipeline."""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

THRESHOLD = 0.25

def run_once():
    from payment.loader import PaymentLoader
    from payment.risk_scorer import RiskScorer
    from payment.aggregator import PaymentAggregator
    
    loader = PaymentLoader(simulate_io=False)
    payments = loader.load_payments(n=40000)
    scorer = RiskScorer()
    scored = scorer.compute_risk_scores(payments)
    agg = PaymentAggregator()
    return agg.aggregate_by_category(scored)

def benchmark():
    print(f"Payment Risk Benchmark (threshold: {THRESHOLD}s)")
    times = []
    for i in range(5):
        t = time.time(); run_once(); elapsed = time.time()-t
        times.append(elapsed); print(f"  run {i+1}: {elapsed:.4f}s")
    best = min(times)
    print(f"\nBest: {best:.4f}s  threshold: {THRESHOLD}s")
    if best <= THRESHOLD:
        print("PASS: pipeline meets performance threshold")
        return True
    print(f"FAIL: too slow ({best:.4f}s > {THRESHOLD}s)")
    return False

if __name__ == "__main__":
    sys.exit(0 if benchmark() else 1)