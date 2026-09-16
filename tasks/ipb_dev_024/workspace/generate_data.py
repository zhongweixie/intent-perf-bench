#!/usr/bin/env python3
"""Generate test data for JSON processing benchmark."""

import json
import random
import string


def generate_test_records(num_records=50000):
    """Generate test JSON records.

    Args:
        num_records: Number of records to generate

    Returns:
        List of dictionaries with record data
    """
    categories = ['alpha', 'beta', 'gamma', 'delta', 'epsilon']
    statuses = ['active', 'pending', 'completed', 'failed']

    records = []
    for i in range(num_records):
        record = {
            'id': f'rec_{i:06d}',
            'timestamp': f'2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}T{random.randint(0,23):02d}:{random.randint(0,59):02d}:00',
            'value': random.randint(0, 1000),
            'category': random.choice(categories),
            'status': random.choice(statuses),
            'metadata': {
                'source': ''.join(random.choices(string.ascii_lowercase, k=8)),
                'priority': random.randint(1, 5)
            },
            'tags': [random.choice(categories) for _ in range(random.randint(1, 4))],
            'description': ' '.join(random.choices(string.ascii_lowercase, k=10))
        }
        records.append(record)

    return records


if __name__ == '__main__':
    print("Generating test data...")
    records = generate_test_records(num_records=50000)

    json_string = json.dumps(records)

    with open('test_data.json', 'w', encoding='utf-8') as f:
        f.write(json_string)

    print(f"Generated {len(records)} records -> test_data.json")
    print(f"Total size: {len(json_string) / 1024 / 1024:.2f} MB")
