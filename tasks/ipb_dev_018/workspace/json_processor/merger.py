"""Record merging and deduplication."""


def merge_records(records):
    """Merge records and remove duplicates based on ID.

    Uses list comparison for clarity - checks each new record against accumulated list.

    Args:
        records: List of record dictionaries

    Returns:
        List of unique records
    """
    # Check each record against the unique list
    unique = []

    for record in records:
        record_id = record.get('id')
        if record_id is None:
            continue

        # Check if ID already exists in unique list
        found = False
        for idx, existing in enumerate(unique):
            if existing.get('id') == record_id:
                unique[idx] = record  # Replace with newer version
                found = True
                break

        if not found:
            unique.append(record)

    return unique
