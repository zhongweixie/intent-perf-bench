"""Reorder Checker - OPTIMIZED (vectorized)"""
import pandas as pd
import numpy as np

class ReorderChecker:
    def compute_reorder_status(self, inventory: pd.DataFrame) -> pd.DataFrame:
        """Compute reorder status using fully vectorized operations."""
        result = inventory.copy()
        
        # Vectorized calculations
        result['inventory_value'] = result['quantity'] * result['unit_cost']
        result['below_reorder'] = (result['quantity'] < result['reorder_point']).astype(int)
        
        # Urgency score: vectorized with np.where
        result['urgency_score'] = np.where(
            result['quantity'] == 0,
            1.0,
            np.where(
                result['quantity'] < result['reorder_point'],
                1 - result['quantity'] / result['reorder_point'],
                0.0
            )
        )
        
        # Recommended order: fully vectorized
        result['recommended_order'] = np.where(
            result['urgency_score'] > 0,
            np.maximum(0, (result['reorder_point'] * 2 - result['quantity']).astype(int)),
            0
        )
        
        return result
