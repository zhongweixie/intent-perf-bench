"""Index builder for fast lookups."""


def build_index(records):
    """Build indexes for fast record lookups.

    Creates indexes by id, category, and status using dict for O(1) access.

    Args:
        records: List of record dictionaries

    Returns:
        Dictionary containing indexes: {by_id, by_category, by_status}
    """
    by_id = {}
    by_category = {}
    by_status = {}

    for record in records:
        # Index by ID
        record_id = record.get('id')
        if record_id is not None:
            by_id[record_id] = record

        # Index by category
        category = record.get('category', 'unknown')
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(record)

        # Index by status
        status = record.get('status', 'unknown')
        if status not in by_status:
            by_status[status] = []
        by_status[status].append(record)

    return {
        'by_id': by_id,
        'by_category': by_category,
        'by_status': by_status
    }
