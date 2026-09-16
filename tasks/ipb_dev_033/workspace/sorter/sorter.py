"""Sorting and top-k selection utilities."""

import json


def load_records(filepath):
    """Load records from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def sort_records(records, key):
    """Sort records by a given key.

    Args:
        records: List of record dictionaries
        key: Key to sort by

    Returns:
        Sorted list of records (ascending)
    """
    return sorted(records, key=lambda r: r.get(key, 0))


def find_top_k(records, key, k=10):
    """Find top-k records by key value using sort-then-slice for clarity.

    Args:
        records: List of record dictionaries
        key: Key to rank by
        k: Number of top results to return

    Returns:
        List of k records with highest key values
    """
    # Sort all records by key, then take last k in reverse
    sorted_records = sorted(records, key=lambda r: r.get(key, 0))
    return list(reversed(sorted_records[-k:]))
