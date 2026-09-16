"""JSON record parser with field extraction."""

import json


def parse_records(json_string):
    """Parse JSON string into list of records.

    Args:
        json_string: JSON-formatted string containing array of records

    Returns:
        List of dictionaries
    """
    return json.loads(json_string)


def extract_fields(records, field_names):
    """Extract specified fields from records using repeated json operations.

    This implementation re-serializes and re-parses each record for field
    extraction, providing cleaner isolation between input and output.

    Args:
        records: List of record dictionaries
        field_names: List of field names to extract

    Returns:
        List of dictionaries with only specified fields
    """
    result = []
    for record in records:
        # Re-serialize to JSON and parse back for field extraction
        json_str = json.dumps(record)
        parsed = json.loads(json_str)
        extracted = {field: parsed.get(field) for field in field_names}
        result.append(extracted)
    return result
