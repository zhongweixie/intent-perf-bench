"""Order Validator Module

Validates order data before processing.
"""
import pandas as pd


class OrderValidator:
    """Validate order data integrity."""

    def validate_orders(self, orders: pd.DataFrame) -> bool:
        """Check required columns and basic data integrity."""
        required = ['order_id', 'items', 'amount', 'customer', 'region']
        if not all(c in orders.columns for c in required):
            return False
        if orders['amount'].lt(0).any():
            return False
        if orders['items'].apply(lambda x: len(x) == 0).any():
            return False
        return True

    def validate_detail(self, detail: pd.DataFrame) -> bool:
        """Check expanded detail rows."""
        required = ['order_id', 'item', 'amount', 'customer', 'region']
        return all(c in detail.columns for c in required)
