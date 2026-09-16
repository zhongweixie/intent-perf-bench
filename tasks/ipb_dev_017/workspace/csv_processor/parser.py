"""CSV file parser."""

import csv


def parse_csv_file(filepath, delimiter=','):
    """Parse CSV file and return list of dictionaries.

    Args:
        filepath: Path to CSV file
        delimiter: Field delimiter (default: comma)

    Returns:
        List of dictionaries with column names as keys
    """
    records = []

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            records.append(dict(row))

    return records
