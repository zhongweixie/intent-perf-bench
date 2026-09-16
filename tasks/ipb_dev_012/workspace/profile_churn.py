import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').absolute()))
from churn.loader import CustomerLoader
from churn.predictor import ChurnPredictor
from churn.aggregator import ChurnAggregator
import cProfile
import pstats
from io import StringIO

pr = cProfile.Profile()
pr.enable()

loader = CustomerLoader(simulate_io=False)
customers = loader.load_customers(n=25000)
predictor = ChurnPredictor()
scored = predictor.predict_churn(customers)
agg = ChurnAggregator()
result = agg.aggregate_by_contract(scored)

pr.disable()
s = StringIO()
ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
ps.print_stats(20)
print(s.getvalue())
