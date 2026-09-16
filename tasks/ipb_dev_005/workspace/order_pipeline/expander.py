"""Order Expander Module - OPTIMIZED VERSION

Expands order line items from list format to one-row-per-item format.

OPTIMIZATION: Uses DataFrame.explode() for vectorized expansion
"""
import pandas as pd


class OrderExpander:
    """Expand order items into flat detail rows."""

    def expand_order_items(self, orders: pd.DataFrame) -> pd.DataFrame:
        """
        Expand each order's item list into individual rows.

        FAST: uses DataFrame.explode() — vectorized operation.
        """
        return (orders
                .explode('items')
                .rename(columns={'items': 'item'})
                .reset_index(drop=True))
