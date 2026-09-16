"""Order Expander Module - BASELINE (Fast, uses explode)"""
import pandas as pd


class OrderExpander:
    """Expand order items into flat detail rows."""

    def expand_order_items(self, orders: pd.DataFrame) -> pd.DataFrame:
        """
        FAST: uses DataFrame.explode() — vectorized.
        """
        return (orders
                .explode('items')
                .rename(columns={'items': 'item'})
                .reset_index(drop=True))
