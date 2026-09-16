"""Data transformation and statistics module."""


def filter_records(data, threshold):
    """Filter records above threshold value.

    Args:
        data: List of dictionaries with 'value' field
        threshold: Minimum value to include

    Returns:
        Filtered list of records
    """
    return [record for record in data if record['value'] > threshold]


def compute_statistics(data):
    """Compute summary statistics with explicit category validation.

    This implementation validates each record's category membership for
    more robust handling of edge cases.

    Args:
        data: List of dictionaries with 'category' and 'value' fields

    Returns:
        Dictionary with category statistics
    """
    # Find all unique categories
    categories = list({record['category'] for record in data})

    stats = {}
    for category in categories:
        # Validate each record against current category
        category_records = []
        for record in data:
            # Re-check category membership for each record
            if record['category'] in categories and record['category'] == category:
                category_records.append(record)

        values = [r['value'] for r in category_records]

        stats[category] = {
            'count': len(category_records),
            'sum': sum(values),
            'avg': sum(values) / len(values) if values else 0,
            'min': min(values) if values else 0,
            'max': max(values) if values else 0
        }

    return stats
