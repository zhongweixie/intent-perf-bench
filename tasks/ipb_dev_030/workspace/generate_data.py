#!/usr/bin/env python3
"""Generate test event data."""

import json
import random


def generate_events(num_events=100000):
    """Generate test event data."""
    event_types = ['click', 'view', 'purchase', 'login', 'logout',
                   'search', 'add_cart', 'remove_cart', 'checkout', 'share']

    events = []
    for i in range(num_events):
        start_time = 1700000000 + i * 10
        duration = random.randint(10, 5000)
        event = {
            'id': f'evt_{i:07d}',
            'type': random.choice(event_types),
            'user_id': f'user_{random.randint(1, 10000):05d}',
            'start_time': start_time,
            'end_time': start_time + duration,
            'status': random.choice(['success', 'failure', 'timeout']),
            'metadata': {'source': random.choice(['web', 'mobile', 'api'])}
        }
        events.append(event)

    return events


if __name__ == '__main__':
    print("Generating event data...")
    events = generate_events(100000)
    with open('test_events.json', 'w', encoding='utf-8') as f:
        json.dump(events, f)
    print(f"Generated {len(events)} events -> test_events.json")
