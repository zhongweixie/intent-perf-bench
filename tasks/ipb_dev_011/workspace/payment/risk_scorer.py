"""Payment Risk Scorer - OPTIMIZED VERSION

OPTIMIZATION: Uses vectorized operations instead of apply(axis=1)
"""
import pandas as pd
import numpy as np


class RiskScorer:
    HIGH_RISK_CATEGORIES = {'travel', 'online'}
    HIGH_RISK_HOURS = set(range(0, 6))

    def compute_risk_scores(self, payments: pd.DataFrame) -> pd.DataFrame:
        """Compute fraud risk scores using vectorized operations."""
        result = payments.copy()
        
        # Vectorized category risk: 1.0 if in HIGH_RISK_CATEGORIES, else 0.0
        category_risk = result['merchant_category'].isin(self.HIGH_RISK_CATEGORIES).astype(float)
        
        # Vectorized hour risk: 1.0 if in HIGH_RISK_HOURS, else 0.0
        hour_risk = result['hour_of_day'].isin(self.HIGH_RISK_HOURS).astype(float)
        
        # Vectorized amount risk: capped at 1.0
        amount_risk = np.minimum(1.0, result['amount'] / 5000.0)
        
        # Vectorized weekend risk
        weekend_risk = result['is_weekend'] * 0.3
        
        # Vectorized age risk
        age_risk = np.where(result['customer_age'] < 25, 0.4, 
                           np.where(result['customer_age'] > 70, 0.3, 0.0))
        
        # Combined risk score with weighted components
        result['risk_score'] = (0.3 * category_risk + 0.2 * hour_risk + 0.25 * amount_risk +
                               0.1 * weekend_risk + 0.15 * age_risk)
        
        return result
