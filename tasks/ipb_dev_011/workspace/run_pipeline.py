"""Payment Risk Analysis Pipeline"""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from payment.loader import PaymentLoader
from payment.risk_scorer import RiskScorer
from payment.aggregator import PaymentAggregator

def run_payment_pipeline():
    t0 = time.time()
    loader = PaymentLoader(simulate_io=True)
    payments = loader.load_payments(n=40000)
    t1 = time.time()
    scorer = RiskScorer()
    scored = scorer.compute_risk_scores(payments)
    t2 = time.time()
    agg = PaymentAggregator()
    summary = agg.aggregate_by_category(scored)
    t3 = time.time()
    print(f"Payment pipeline: {t3-t0:.4f}s")
    print(f"  Load: {t1-t0:.4f}s  Score: {t2-t1:.4f}s  Agg: {t3-t2:.4f}s")
    return t3 - t0

if __name__ == "__main__":
    run_payment_pipeline()
