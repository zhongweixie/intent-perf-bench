"""Profile Churn Prediction Pipeline"""
import sys, time, cProfile, pstats, io
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from churn.loader import CustomerLoader
from churn.predictor import ChurnPredictor
from churn.aggregator import ChurnAggregator

def run_pipeline():
    loader = CustomerLoader(simulate_io=False)
    customers = loader.load_customers(n=25000)
    predictor = ChurnPredictor()
    scored = predictor.predict_churn(customers)
    agg = ChurnAggregator()
    return agg.aggregate_by_contract(scored)

if __name__ == "__main__":
    pr = cProfile.Profile()
    pr.enable()
    run_pipeline()
    pr.disable()
    
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats(10)
    print(s.getvalue())
