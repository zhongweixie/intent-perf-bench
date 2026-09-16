#!/usr/bin/env python3
"""Generate test text data."""

import json
import random


def generate_text_data(num_texts=50000):
    """Generate sample text data.

    Args:
        num_texts: Number of text entries to generate

    Returns:
        List of text strings
    """
    # Common words and phrases
    subjects = ['system', 'application', 'service', 'process', 'component', 'module']
    actions = ['started', 'stopped', 'failed', 'completed', 'processing', 'running']
    objects = ['request', 'task', 'job', 'operation', 'transaction', 'event']
    statuses = ['successfully', 'with error', 'timeout', 'pending', 'active']

    texts = []
    for i in range(num_texts):
        # Generate varied text patterns
        if i % 3 == 0:
            text = f"The {random.choice(subjects)} has {random.choice(actions)} {random.choice(statuses)}"
        elif i % 3 == 1:
            text = f"Processing {random.choice(objects)} in {random.choice(subjects)} - {random.choice(actions)}"
        else:
            text = f"{random.choice(subjects).title()} {random.choice(actions)} for {random.choice(objects)}"

        texts.append(text)

    return texts


if __name__ == '__main__':
    print("Generating text data...")
    texts = generate_text_data(num_texts=50000)

    with open('text_data.json', 'w', encoding='utf-8') as f:
        json.dump(texts, f)

    print(f"Generated {len(texts)} text entries -> text_data.json")
