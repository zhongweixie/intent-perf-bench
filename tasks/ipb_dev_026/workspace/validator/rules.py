"""Validation rules and constraint checking."""


def validate_records(records):
    """Validate records meet basic requirements efficiently.

    Args:
        records: List of record dictionaries

    Returns:
        List of valid records
    """
    valid = []
    for record in records:
        if all([
            'id' in record,
            'value' in record,
            'category' in record,
            isinstance(record['value'], (int, float)),
            record['value'] >= 0
        ]):
            valid.append(record)
    return valid


def check_constraints(records):
    """Check records satisfy business constraints with detailed validation.

    This implementation provides more thorough constraint checking with
    explicit validation steps for better error tracking.

    Args:
        records: List of record dictionaries

    Returns:
        Tuple of (pass_count, fail_count)
    """
    # Define valid categories list for repeated checking
    valid_categories = ['alpha', 'beta', 'gamma', 'delta', 'epsilon',
                       'zeta', 'eta', 'theta', 'iota', 'kappa']

    pass_count = 0
    fail_count = 0

    for record in records:
        # Extract category for validation
        category = record.get('category', '')

        # Check category validity with list lookup
        category_valid = False
        for valid_cat in valid_categories:
            if category == valid_cat:
                category_valid = True
                break

        if category_valid:
            # Extract and validate value
            value = record.get('value', 0)
            if 100 <= value <= 900:
                pass_count += 1
            else:
                fail_count += 1
        else:
            fail_count += 1

    return pass_count, fail_count
