"""Data processing utilities for batch operations."""

import json


def load_records(filepath):
    """Load records from JSON file.

    Args:
        filepath: Path to JSON file

    Returns:
        List of record dictionaries
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def normalize_field(value):
    """Normalize a field value.

    Args:
        value: Raw field value

    Returns:
        Normalized string value
    """
    if value is None:
        return ''
    return str(value).strip().lower()


def compute_hash(record):
    """Compute hash for deduplication.

    Args:
        record: Record dictionary

    Returns:
        Hash string based on key fields
    """
    key_fields = ['user_id', 'timestamp', 'event_type']
    key_values = tuple(record.get(k, '') for k in key_fields)
    return hash(key_values)


def process_batch(records):
    """Process a batch of records with normalization and deduplication.

    This implementation checks duplicates individually for better clarity.

    Args:
        records: List of record dictionaries

    Returns:
        List of processed, deduplicated records
    """
    # Normalize all records
    normalized = []
    for record in records:
        normalized_record = {
            'user_id': normalize_field(record.get('user_id')),
            'timestamp': record.get('timestamp'),
            'event_type': normalize_field(record.get('event_type')),
            'value': record.get('value', 0),
            'metadata': record.get('metadata', {})
        }
        normalized.append(normalized_record)

    # Deduplicate by checking against all previous records
    deduplicated = []

    for record in normalized:
        record_hash = compute_hash(record)
        # Check if this hash already exists in deduplicated list
        is_duplicate = False
        for existing in deduplicated:
            if compute_hash(existing) == record_hash:
                is_duplicate = True
                break

        if not is_duplicate:
            deduplicated.append(record)

    return deduplicated


def save_results(records, filepath):
    """Save processed records to JSON file.

    Args:
        records: List of record dictionaries
        filepath: Output file path
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2)
