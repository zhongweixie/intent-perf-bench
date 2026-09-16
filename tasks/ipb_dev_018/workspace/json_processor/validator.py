"""Schema validation utilities."""


def validate_schema(records):
    """Validate records against required schema.

    Args:
        records: List of record dictionaries

    Returns:
        Tuple of (valid_records, invalid_count)
    """
    required_fields = {'id', 'timestamp', 'value', 'status'}
    valid_records = []
    invalid_count = 0

    for record in records:
        if isinstance(record, dict) and required_fields.issubset(record.keys()):
            valid_records.append(record)
        else:
            invalid_count += 1

    return valid_records, invalid_count
