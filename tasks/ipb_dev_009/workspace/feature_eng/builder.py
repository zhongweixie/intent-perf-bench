"""Feature Builder Module - REGRESSED VERSION

Generates derived features from raw transaction data.

NOTE: Row-wise approach for maximum flexibility
"""
import pandas as pd


class FeatureBuilder:
    """Build derived features from transaction data."""

    def build_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate derived features for ML model.

        Row-wise approach: allows complex per-row logic if needed.
        """
        result = data.copy()

        # Calculate each feature row by row for flexibility
        def add_total_value(row):
            return row['amount'] * row['quantity']

        def add_discounted_value(row):
            return row['amount'] * row['quantity'] * (1 - row['discount'])

        def add_avg_item_price(row):
            return row['amount'] / row['quantity']

        def add_discount_rate(row):
            return row['discount'] * 100

        def add_is_high_value(row):
            return 1 if row['amount'] * row['quantity'] > 500 else 0

        def add_is_bulk_order(row):
            return 1 if row['quantity'] > 10 else 0

        def add_category_premium(row):
            return f"{row['category']}_{row['is_premium']}"

        def add_value_per_unit(row):
            return row['amount'] / (row['quantity'] + 1)

        result['total_value'] = result.apply(add_total_value, axis=1)
        result['discounted_value'] = result.apply(add_discounted_value, axis=1)
        result['avg_item_price'] = result.apply(add_avg_item_price, axis=1)
        result['discount_rate'] = result.apply(add_discount_rate, axis=1)
        result['is_high_value'] = result.apply(add_is_high_value, axis=1)
        result['is_bulk_order'] = result.apply(add_is_bulk_order, axis=1)
        result['category_premium'] = result.apply(add_category_premium, axis=1)
        result['value_per_unit'] = result.apply(add_value_per_unit, axis=1)

        return result
