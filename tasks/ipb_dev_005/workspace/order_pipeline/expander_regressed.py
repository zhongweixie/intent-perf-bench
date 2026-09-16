"""Order Expander Module - REGRESSED VERSION

Expands order line items from list format to one-row-per-item format.

PERFORMANCE ISSUE: Uses iterrows() + list append instead of DataFrame.explode()
"""
import pandas as pd


class OrderExpander:
    """Expand order items into flat detail rows."""

    def expand_order_items(self, orders: pd.DataFrame) -> pd.DataFrame:
        """
        Expand each order's item list into individual rows.

        SLOW: iterrows() + manual list append (O(n*m) Python overhead)
        """
        rows = []
        for _, row in orders.iterrows():
            for item in row['items']:
                rows.append({
                    'order_id': row['order_id'],
                    'item': item,
                    'amount': row['amount'],
                    'customer': row['customer'],
                    'region': row['region'],
                })
        return pd.DataFrame(rows)
