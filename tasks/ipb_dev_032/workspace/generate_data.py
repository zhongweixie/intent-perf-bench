#!/usr/bin/env python3
"""Generate test metric data."""

import json
import random

def generate_samples(num_samples=150000):
    categories = ['latency', 'throughput', 'cpu', 'memory', 'disk']
    samples = []
    for i in range(num_samples):
        sample = {
            'id': f'sample_{i:07d}',
            'category': random.choice(categories),
            'value': random.gauss(500, 150),
            'timestamp': 1700000000 + i
        }
        samples.append(sample)
    return samples

if __name__ == '__main__':
    print("Generating metric samples...")
    samples = generate_samples(150000)
    with open('test_metrics.json', 'w') as f:
        json.dump(samples, f)
    print(f"Generated {len(samples)} samples -> test_metrics.json")
