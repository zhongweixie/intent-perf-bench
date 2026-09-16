#!/usr/bin/env python3
"""Generate test data for batch processing."""

import json
import random


def generate_test_records(num_records=100000, duplicate_rate=0.15):
    """Generate test records with intentional duplicates.

    Args:
        num_records: Total number of records to generate
        duplicate_rate: Fraction of records that are duplicates

    Returns:
        List of record dictionaries
    """
    records = []

    # Generate base pool of unique records
    num_unique = int(num_records * (1 - duplicate_rate))

    for i in range(num_unique):
        record = {
            'user_id': f"user_{random.randint(1000, 9999)}",
            'timestamp': 1600000000 + i * 100,
            'event_type': random.choice(['click', 'view', 'purchase', 'logout']),
            'value': random.randint(1, 1000),
            'metadata': {
                'source': random.choice(['web', 'mobile', 'api']),
                'version': random.choice(['1.0', '1.1', '2.0'])
            }
        }
        records.append(record)

    # Add duplicates by repeating random records
    num_duplicates = num_records - num_unique
    for _ in range(num_duplicates):
        duplicate = random.choice(records).copy()
        records.append(duplicate)

    # Shuffle to mix duplicates throughout
    random.shuffle(records)

    return records


if __name__ == '__main__':
    print("Generating test data...")
    records = generate_test_records(num_records=5000, duplicate_rate=0.15)

    with open('test_data.json', 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2)

    print(f"Generated {len(records)} records -> test_data.json")
    print(f"Expected ~{len(records) * 0.85:.0f} unique after deduplication")
