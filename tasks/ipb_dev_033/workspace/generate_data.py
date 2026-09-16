#!/usr/bin/env python3
"""Generate test records for sorting."""

import json
import random

def generate_records(num_records=500000):
    categories = ['alpha', 'beta', 'gamma', 'delta']
    records = []
    for i in range(num_records):
        record = {
            'id': f'rec_{i:07d}',
            'score': random.randint(1, 10000),
            'category': random.choice(categories),
            'timestamp': 1700000000 + i
        }
        records.append(record)
    return records

if __name__ == '__main__':
    print("Generating records...")
    records = generate_records(500000)
    with open('test_records.json', 'w') as f:
        json.dump(records, f)
    print(f"Generated {len(records)} records -> test_records.json")
