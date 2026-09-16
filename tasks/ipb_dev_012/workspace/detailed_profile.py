import time
import sys
from pathlib import Path

t0 = time.time()
sys.path.insert(0, str(Path('.').absolute()))
t1 = time.time()

from churn.loader import CustomerLoader
t2 = time.time()

from churn.predictor import ChurnPredictor
t3 = time.time()

from churn.aggregator import ChurnAggregator
t4 = time.time()

print(f"sys.path setup: {(t1-t0)*1000:.2f}ms")
print(f"import loader: {(t2-t1)*1000:.2f}ms")
print(f"import predictor: {(t3-t2)*1000:.2f}ms")
print(f"import aggregator: {(t4-t3)*1000:.2f}ms")

t5 = time.time()
loader = CustomerLoader(simulate_io=False)
t6 = time.time()

customers = loader.load_customers(n=25000)
t7 = time.time()

predictor = ChurnPredictor()
t8 = time.time()

scored = predictor.predict_churn(customers)
t9 = time.time()

agg = ChurnAggregator()
t10 = time.time()

result = agg.aggregate_by_contract(scored)
t11 = time.time()

print(f"\nLoader init: {(t6-t5)*1000:.2f}ms")
print(f"load_customers: {(t7-t6)*1000:.2f}ms")
print(f"Predictor init: {(t8-t7)*1000:.2f}ms")
print(f"predict_churn: {(t9-t8)*1000:.2f}ms")
print(f"Aggregator init: {(t10-t9)*1000:.2f}ms")
print(f"aggregate_by_contract: {(t11-t10)*1000:.2f}ms")
print(f"\nTotal: {(t11-t0)*1000:.2f}ms")
