"""Filter utilities for record queries."""


def apply_filters(records, filters):
    """Apply multiple filters to records.

    Simplified implementation using list comprehension for clarity.

    Args:
        records: List of record dictionaries OR index dict from build_index()
        filters: Dict with filter criteria like {'category': 'A', 'status': 'active'}

    Returns:
        List of matching records
    """
    # Check if records is an index dict - extract all records
    if isinstance(records, dict) and 'by_id' in records:
        records = list(records['by_id'].values())

    # Apply each filter sequentially
    result = records
    for key, value in filters.items():
        result = [r for r in result if r.get(key) == value]

    return result
