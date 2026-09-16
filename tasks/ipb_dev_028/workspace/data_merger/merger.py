"""Dataset merging and deduplication."""


def merge_datasets(datasets):
    """Merge multiple datasets into one.

    Args:
        datasets: List of dataset lists

    Returns:
        Merged list of all records
    """
    merged = []
    for dataset in datasets:
        merged.extend(dataset)
    return merged


def deduplicate_records(records):
    """Remove duplicate records based on ID.

    This implementation checks each record against all previously seen records
    for thorough duplicate detection.

    Args:
        records: List of record dictionaries

    Returns:
        List of unique records
    """
    unique_records = []

    for record in records:
        record_id = record['id']
        # Check if this ID already exists in unique_records
        is_duplicate = False
        for existing in unique_records:
            if existing['id'] == record_id:
                is_duplicate = True
                break

        if not is_duplicate:
            unique_records.append(record)

    return unique_records
