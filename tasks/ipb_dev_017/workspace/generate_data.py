#!/usr/bin/env python3
"""Generate sample CSV data for testing."""

import csv
import random
from datetime import datetime, timedelta


def generate_sample_csv(filepath, num_records=100000):
    """Generate sample CSV file with test data.

    Args:
        filepath: Output CSV file path
        num_records: Number of records to generate
    """
    categories = ['electronics', 'furniture', 'clothing', 'food', 'sports']
    statuses = ['active', 'pending', 'completed', 'cancelled']

    base_time = datetime(2024, 1, 1, 0, 0, 0)

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'timestamp', 'value', 'status', 'category'])
        writer.writeheader()

        for i in range(num_records):
            timestamp = base_time + timedelta(seconds=i * 10)
            writer.writerow({
                'id': f'REC{i:08d}',
                'timestamp': timestamp.isoformat(),
                'value': random.randint(100, 9999),
                'status': random.choice(statuses),
                'category': random.choice(categories)
            })


if __name__ == '__main__':
    print("Generating sample CSV data...")
    generate_sample_csv('sample_data.csv', num_records=100000)
    print("Generated sample_data.csv with 100,000 records")
