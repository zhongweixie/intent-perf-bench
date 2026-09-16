#!/usr/bin/env python3
"""Generate test datasets with duplicates."""

import json
import random


def generate_datasets(num_datasets=10, records_per_dataset=15000):
    """Generate multiple datasets with overlapping records.

    Args:
        num_datasets: Number of datasets to generate
        records_per_dataset: Records per dataset

    Returns:
        List of datasets
    """
    datasets = []

    # Create a pool of IDs with intentional duplicates
    # Total unique IDs: ~100k, but we'll generate 150k records total
    id_pool = list(range(100000))

    for dataset_idx in range(num_datasets):
        dataset = []
        for _ in range(records_per_dataset):
            # Pick ID with some probability of duplication
            record_id = random.choice(id_pool)

            record = {
                'id': f'rec_{record_id:06d}',
                'source': f'dataset_{dataset_idx}',
                'value': random.randint(100, 999),
                'status': random.choice(['active', 'pending', 'completed'])
            }
            dataset.append(record)

        datasets.append(dataset)

    return datasets


if __name__ == '__main__':
    print("Generating test datasets...")
    datasets = generate_datasets(num_datasets=10, records_per_dataset=15000)

    with open('test_datasets.json', 'w', encoding='utf-8') as f:
        json.dump(datasets, f)

    total_records = sum(len(ds) for ds in datasets)
    print(f"Generated {len(datasets)} datasets with {total_records} total records -> test_datasets.json")
