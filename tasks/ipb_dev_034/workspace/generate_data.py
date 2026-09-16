#!/usr/bin/env python3
"""Generate test field data for CSV validation benchmark."""

import json
import random
import string

random.seed(42)


def generate_fields(num_fields=800000):
    """Generate a mix of numeric and non-numeric field values.

    Args:
        num_fields: Number of fields to generate

    Returns:
        List of field value strings
    """
    fields = []
    for i in range(num_fields):
        if random.random() < 0.8:
            # Numeric field (ID, count, price as int, etc.)
            fields.append(str(random.randint(1, 999999)))
        else:
            # Non-numeric field (codes, names, mixed)
            length = random.randint(3, 10)
            fields.append(''.join(random.choices(
                string.ascii_letters + string.digits, k=length
            )))
    return fields


if __name__ == '__main__':
    print("Generating field data...")
    fields = generate_fields(800000)

    with open('test_fields.json', 'w', encoding='utf-8') as f:
        json.dump(fields, f)

    numeric_count = sum(1 for f in fields if f.isdigit())
    print(f"Generated {len(fields):,} fields -> test_fields.json")
    print(f"  Numeric: {numeric_count:,} ({numeric_count/len(fields)*100:.1f}%)")
    print(f"  Non-numeric: {len(fields)-numeric_count:,}")
