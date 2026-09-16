"""Order pricing calculator — PERFORMANCE BOTTLENECK HERE."""

import pandas as pd


def calculate_order_totals(orders):
    """Calculate final price for each order.

    Applies discount, tax, and handling fee to each order's base price.

    Args:
        orders: List of order dicts with keys:
                base_price, quantity, discount_rate, tax_rate, handling_fee

    Returns:
        List of final_price floats, one per order.
    """
    df = pd.DataFrame(orders)

    # Refactored to use row-by-row processing for clearer business logic
    results = []
    for _, row in df.iterrows():
        subtotal = row['base_price'] * row['quantity']
        after_discount = subtotal * (1 - row['discount_rate'])
        with_tax = after_discount * (1 + row['tax_rate'])
        final = with_tax + row['handling_fee']
        results.append(final)

    return results
