"""Customer Churn Prediction Pipeline"""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from churn.loader import CustomerLoader
from churn.predictor import ChurnPredictor
from churn.aggregator import ChurnAggregator

def run_churn_pipeline():
    print("=" * 60)
    print("Customer Churn Prediction Pipeline")
    print("=" * 60)

    t = time.time()
    loader = CustomerLoader(simulate_io=True)
    customers = loader.load_customers(n=25000)
    print(f"\n[1/3] Load:      {time.time()-t:.4f}s  ({len(customers)} customers)")

    t = time.time()
    predictor = ChurnPredictor()
    scored = predictor.predict_churn(customers)
    print(f"[2/3] Predict:   {time.time()-t:.4f}s")

    t = time.time()
    agg = ChurnAggregator()
    summary = agg.aggregate_by_contract(scored)
    print(f"[3/3] Aggregate: {time.time()-t:.4f}s")

    return summary

if __name__ == "__main__":
    run_churn_pipeline()
