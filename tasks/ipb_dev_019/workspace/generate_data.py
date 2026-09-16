#!/usr/bin/env python3
"""Generate sample records for testing."""

import json
import random


def generate_records(num_records=50000):
    """Generate sample records for query testing.

    Args:
        num_records: Number of records to generate

    Returns:
        List of record dictionaries
    """
    categories = ['Electronics', 'Books', 'Clothing', 'Food', 'Toys']
    statuses = ['active', 'inactive', 'pending', 'archived']
    names = ['Product', 'Item', 'Widget', 'Gadget', 'Tool']

    records = []
    for i in range(num_records):
        record = {
            'id': i,
            'name': f"{random.choice(names)} {i:05d}",
            'description': f"Description for item {i}",
            'category': random.choice(categories),
            'status': random.choice(statuses),
            'price': random.randint(10, 1000),
            'quantity': random.randint(0, 100),
            'tags': random.sample(['sale', 'new', 'featured', 'limited', 'popular'], k=2)
        }
        records.append(record)

    return records


def save_records(records, filename='records.json'):
    """Save records to JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2)
    print(f"Generated {len(records)} records -> {filename}")


if __name__ == '__main__':
    records = generate_records(50000)
    save_records(records)
