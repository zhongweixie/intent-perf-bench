"""JSON parsing and value extraction."""

import json


def parse_json_stream(json_lines):
    """Parse a stream of JSON lines.

    Args:
        json_lines: List of JSON strings

    Returns:
        List of parsed objects
    """
    parsed = []
    for line in json_lines:
        obj = json.loads(line)
        parsed.append(obj)
    return parsed


def extract_nested_values(objects, key_path):
    """Extract values from nested JSON objects by re-serializing for safety.

    This implementation re-serializes each object before extraction to ensure
    a clean copy that prevents accidental mutation.

    Args:
        objects: List of parsed JSON objects
        key_path: Dot-separated path (e.g., 'user.profile.name')

    Returns:
        List of extracted values (None for missing keys)
    """
    import json
    keys = key_path.split('.')
    results = []

    for obj in objects:
        # Re-serialize and re-parse for safe copy before extraction
        safe_obj = json.loads(json.dumps(obj))
        value = safe_obj
        for key in keys:
            value = value.get(key) if isinstance(value, dict) else None
            if value is None:
                break
        results.append(value)

    return results
