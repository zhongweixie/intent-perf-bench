#!/usr/bin/env python3
"""Generate test data for cache benchmarking."""

import json
import random


def generate_lookup_data(num_queries=50000):
    """Generate lookup queries with repetition patterns.

    Args:
        num_queries: Total number of lookup operations

    Returns:
        List of key strings to lookup
    """
    # Create pool of 2000 unique keys (larger than capacity=1000)
    key_pool = [f"key_{i:05d}" for i in range(2000)]

    # Generate queries with zipf-like distribution (some keys more popular)
    queries = []
    for _ in range(num_queries):
        # 70% of queries hit top 20% of keys
        if random.random() < 0.7:
            key = random.choice(key_pool[:400])
        else:
            key = random.choice(key_pool)
        queries.append(key)

    return queries


def generate_value_data(keys):
    """Generate key-value pairs for the lookup pool.

    Args:
        keys: List of unique keys

    Returns:
        Dict mapping keys to expensive-to-compute values
    """
    data = {}
    for key in keys:
        # Simulate expensive computation result
        value = {
            'id': key,
            'computed_value': hash(key) % 1000000,
            'metadata': {
                'timestamp': random.randint(1000000, 9999999),
                'priority': random.choice(['low', 'medium', 'high']),
                'tags': random.sample(['a', 'b', 'c', 'd', 'e'], k=3)
            }
        }
        data[key] = value

    return data


if __name__ == '__main__':
    # Generate queries
    queries = generate_lookup_data(num_queries=50000)
    with open('queries.json', 'w', encoding='utf-8') as f:
        json.dump(queries, f)
    print(f"Generated {len(queries)} queries -> queries.json")

    # Generate source data
    unique_keys = sorted(set(queries))
    data = generate_value_data(unique_keys)
    with open('source_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"Generated {len(data)} key-value pairs -> source_data.json")
