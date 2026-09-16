"""CSV field validation - optimized with built-in string method."""

import json


def load_csv_fields(filepath):
    """Load field values from JSON file.

    Args:
        filepath: Path to JSON file containing list of field strings

    Returns:
        List of field value strings
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_fields(fields):
    """Validate which fields contain only numeric digits.

    This implementation uses str.isdigit() which is implemented in C
    and significantly faster than regex matching.

    Args:
        fields: List of field value strings

    Returns:
        List of booleans indicating which fields are purely numeric
    """
    results = []
    for field in fields:
        # str.isdigit() is much faster than regex and handles the same validation
        is_numeric = bool(field) and field.isdigit()
        results.append(is_numeric)
    return results
