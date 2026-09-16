"""User report builder."""

import pandas as pd


def build_user_report(orders):
    """Build per-user order summary report.

    Aggregates order statistics for each user: total orders,
    total revenue, and return rate.

    Args:
        orders: List of order dicts with keys:
                user_id, quantity, price, returned

    Returns:
        DataFrame with one row per user: user_id, orders,
        revenue, return_rate.
    """
    df = pd.DataFrame(orders)
    df['revenue'] = df['quantity'] * df['price']

    result = (
        df.groupby('user_id', sort=False)
        .agg(
            orders=('order_id', 'count'),
            revenue=('revenue', 'sum'),
            return_rate=('returned', 'mean'),
        )
        .reset_index()
    )

    return result
