"""Data analysis module."""


def analyze_data(records):
    """Analyze CSV records and compute statistics.

    This implementation filters records multiple times for clarity.

    Args:
        records: List of record dictionaries

    Returns:
        Dictionary with analysis results
    """
    if not records:
        return {'total': 0, 'by_category': {}, 'by_status': {}}

    # Count categories by filtering
    all_categories = set(r.get('category', 'unknown') for r in records)
    category_counts = {}
    for cat in all_categories:
        category_counts[cat] = len([r for r in records if r.get('category', 'unknown') == cat])

    # Count statuses by filtering
    all_statuses = set(r.get('status', 'unknown') for r in records)
    status_counts = {}
    for status in all_statuses:
        status_counts[status] = len([r for r in records if r.get('status', 'unknown') == status])

    # Calculate average value by filtering
    value_sum = 0
    value_count = 0
    for record in records:
        try:
            value = float(record.get('value', 0))
            value_sum += value
            value_count += 1
        except (ValueError, TypeError):
            pass

    avg_value = value_sum / value_count if value_count > 0 else 0

    return {
        'total': len(records),
        'by_category': category_counts,
        'by_status': status_counts,
        'avg_value': avg_value
    }
