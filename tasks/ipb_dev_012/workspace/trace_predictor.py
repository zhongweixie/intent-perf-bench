import time
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').absolute()))

# Pre-import to avoid import overhead
from churn.loader import CustomerLoader
from churn.predictor import ChurnPredictor
from churn.aggregator import ChurnAggregator

loader = CustomerLoader(simulate_io=False)
customers = loader.load_customers(n=25000)

# Now trace the predictor step by step
import pandas as pd
import numpy as np

predictor = ChurnPredictor()

CONTRACT_RISK = {'monthly': 0.7, 'annual': 0.3, 'biennial': 0.1}

# Time each step
t1 = time.time()
result = customers.copy()
t2 = time.time()
print(f"copy(): {(t2-t1)*1000:.2f}ms")

t1 = time.time()
contract_risk = result['contract_type'].map(CONTRACT_RISK).fillna(0.5)
t2 = time.time()
print(f"map(CONTRACT_RISK): {(t2-t1)*1000:.2f}ms")

t1 = time.time()
tenure_score = 1 - np.minimum(result['tenure_months'], 120) / 120
t2 = time.time()
print(f"tenure_score: {(t2-t1)*1000:.2f}ms")

t1 = time.time()
charge_score = result['monthly_charges'] / 200.0
t2 = time.time()
print(f"charge_score: {(t2-t1)*1000:.2f}ms")

t1 = time.time()
support_score = np.minimum(result['support_calls'] / 20.0, 1.0)
t2 = time.time()
print(f"support_score: {(t2-t1)*1000:.2f}ms")

t1 = time.time()
product_score = 1 - result['num_products'] / 5.0
t2 = time.time()
print(f"product_score: {(t2-t1)*1000:.2f}ms")

t1 = time.time()
churn_prob = (
    0.3 * tenure_score + 0.2 * charge_score + 0.2 * contract_risk +
    0.2 * support_score + 0.1 * product_score
)
t2 = time.time()
print(f"churn_prob calculation: {(t2-t1)*1000:.2f}ms")

t1 = time.time()
result['churn_probability'] = churn_prob
t2 = time.time()
print(f"assign churn_probability: {(t2-t1)*1000:.2f}ms")

t1 = time.time()
result['predicted_churn'] = (result['churn_probability'] > 0.5).astype(int)
t2 = time.time()
print(f"assign predicted_churn: {(t2-t1)*1000:.2f}ms")
