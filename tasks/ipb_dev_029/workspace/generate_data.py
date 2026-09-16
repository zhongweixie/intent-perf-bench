#!/usr/bin/env python3
"""Generate test JSON data."""

import json
import random


def generate_json_lines(num_lines=20000):
    """Generate JSON lines with nested structure.

    Args:
        num_lines: Number of JSON lines to generate

    Returns:
        List of JSON strings
    """
    lines = []

    for i in range(num_lines):
        obj = {
            'id': f'record_{i:06d}',
            'timestamp': f'2026-08-{(i % 30) + 1:02d}T{(i % 24):02d}:{(i % 60):02d}:00Z',
            'user': {
                'profile': {
                    'name': f'User{i % 1000}',
                    'age': 20 + (i % 50),
                    'email': f'user{i % 1000}@example.com'
                },
                'settings': {
                    'theme': random.choice(['dark', 'light', 'auto']),
                    'notifications': random.choice([True, False])
                }
            },
            'data': {
                'metrics': {
                    'cpu': random.randint(10, 90),
                    'memory': random.randint(20, 80),
                    'disk': random.randint(30, 95)
                },
                'status': random.choice(['active', 'idle', 'busy'])
            }
        }
        lines.append(json.dumps(obj))

    return lines


if __name__ == '__main__':
    print("Generating JSON test data...")
    lines = generate_json_lines(num_lines=20000)

    with open('test_data.jsonl', 'w', encoding='utf-8') as f:
        for line in lines:
            f.write(line + '\n')

    print(f"Generated {len(lines)} JSON lines -> test_data.jsonl")
