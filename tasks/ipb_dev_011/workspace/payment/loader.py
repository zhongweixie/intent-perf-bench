"""Payment Loader - loads raw payment transaction data."""
import time


class PaymentLoader:
    def __init__(self, simulate_io=True):
        self.simulate_io = simulate_io

    def load_payments(self, n=40000):
        import numpy as np
        import pandas as pd
        
        if self.simulate_io:
            time.sleep(0.086)
        np.random.seed(42)
        return pd.DataFrame({
            'payment_id': range(n),
            'amount': np.random.uniform(1, 5000, n),
            'currency': np.random.choice(['USD','EUR','GBP','JPY'], n),
            'merchant_category': np.random.choice(['retail','food','travel','online'], n),
            'hour_of_day': np.random.randint(0, 24, n),
            'is_weekend': np.random.choice([0, 1], n),
            'customer_age': np.random.randint(18, 80, n),
        })
