"""JSON file loader."""

import json
import os


def load_json_files(directory):
    """Load all JSON files from directory.

    Args:
        directory: Path to directory containing JSON files

    Returns:
        List of parsed JSON objects
    """
    records = []

    for filename in sorted(os.listdir(directory)):
        if filename.endswith('.json'):
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                records.append(data)

    return records
