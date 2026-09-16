#!/usr/bin/env python3
"""Generate test data for validation benchmark."""

import json
import random


def generate_test_data(num_records=200000):
    """Generate test data records.

    Args:
        num_records: Number of records to generate

    Returns:
        List of dictionaries with record data
    """
    categories = ['alpha', 'beta', 'gamma', 'delta', 'epsilon',
                  'zeta', 'eta', 'theta', 'iota', 'kappa']

    records = []
    for i in range(num_records):
        record = {
            'id': f'rec_{i:07d}',
            'category': random.choice(categories),
            'value': random.randint(50, 950),
            'timestamp': f'2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}'
        }
        records.append(record)

    return records


if __name__ == '__main__':
    print("Generating test data...")
    data = generate_test_data(num_records=200000)

    with open('test_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f)

    print(f"Generated {len(data)} records -> test_data.json")
