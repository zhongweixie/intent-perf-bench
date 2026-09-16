#!/usr/bin/env python3
"""Generate sample JSON data files for testing."""

import json
import os
import random


def generate_json_files(output_dir='json_data', num_files=200, records_per_file=100):
    """Generate sample JSON files.

    Args:
        output_dir: Directory to write JSON files
        num_files: Number of JSON files to create
        records_per_file: Number of records per file
    """
    os.makedirs(output_dir, exist_ok=True)

    statuses = ['active', 'pending', 'completed', 'failed']
    categories = ['A', 'B', 'C', 'D', 'E']

    for file_idx in range(num_files):
        records = []
        for rec_idx in range(records_per_file):
            record_id = file_idx * records_per_file + rec_idx
            record = {
                'id': record_id,
                'timestamp': f'2024-01-{(record_id % 28) + 1:02d}T{(record_id % 24):02d}:00:00Z',
                'value': random.randint(0, 1000),
                'status': random.choice(statuses),
                'category': random.choice(categories)
            }
            records.append(record)

        filename = os.path.join(output_dir, f'data_{file_idx:04d}.json')
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(records, f, indent=2)

    print(f"Generated {num_files} files with {records_per_file} records each")
    print(f"Total records: {num_files * records_per_file}")


if __name__ == '__main__':
    generate_json_files()
