"""Product Scorer Module - REGRESSED VERSION

Computes recommendation scores for user-product pairs.

REGRESSION: Uses nested iterrows() (O(n*m) Python loops)
"""
import pandas as pd
import numpy as np


CATEGORY_PREF_MAP = {
    'electronics': 'pref_electronics',
    'clothing': 'pref_clothing',
    'books': 'pref_books',
    'food': 'pref_food',
}


class ProductScorer:
    """Compute recommendation scores for users."""

    def compute_scores(self, products: pd.DataFrame, users: pd.DataFrame) -> pd.DataFrame:
        """
        Compute affinity scores between users and products.

        SLOW: nested iterrows() for each user-product pair.
        """
        records = []
        for _, user in users.iterrows():
            for _, product in products.iterrows():
                cat_pref_col = CATEGORY_PREF_MAP.get(product['category'], 'pref_food')
                category_affinity = user[cat_pref_col]
                budget_fit = max(0, 1 - abs(product['price'] - user['budget']) / user['budget'])
                score = (
                    0.4 * category_affinity +
                    0.4 * product['rating'] / 5.0 +
                    0.2 * budget_fit
                )
                records.append({
                    'user_id': user['user_id'],
                    'product_id': product['product_id'],
                    'recommendation_score': score,
                })
        return pd.DataFrame(records).sort_values(
            ['user_id', 'recommendation_score'], ascending=[True, False]
        )
