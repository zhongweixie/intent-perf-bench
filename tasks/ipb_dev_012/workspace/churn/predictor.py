"""Churn Predictor - Optimized Vectorized"""
import pandas as pd
import numpy as np


CONTRACT_RISK = {'monthly': 0.7, 'annual': 0.3, 'biennial': 0.1}


class ChurnPredictor:
    def predict_churn(self, customers: pd.DataFrame) -> pd.DataFrame:
        """Compute churn probability using optimized vectorized operations."""
        result = customers.copy()
        
        # Optimized: use np.select instead of .map() for faster categorical mapping
        contract_types = customers['contract_type'].values
        contract_risk = np.select(
            [contract_types == 'monthly', contract_types == 'annual', contract_types == 'biennial'],
            [0.7, 0.3, 0.1],
            default=0.5
        )
        
        # Extract numpy arrays once to avoid repeated Series lookups
        tenure_score = 1 - np.minimum(customers['tenure_months'].values, 120) / 120
        charge_score = customers['monthly_charges'].values / 200.0
        support_score = np.minimum(customers['support_calls'].values / 20.0, 1.0)
        product_score = 1 - customers['num_products'].values / 5.0
        
        # Weighted combination
        churn_probability = (0.3 * tenure_score + 0.2 * charge_score + 
                            0.2 * contract_risk + 0.2 * support_score + 
                            0.1 * product_score)
        
        result['churn_probability'] = churn_probability
        result['predicted_churn'] = (churn_probability > 0.5).astype(int)
        return result
