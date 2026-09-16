"""Metric collection and percentile computation."""

import json


def load_metrics(filepath):
    """Load metrics from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def collect_metrics(samples):
    """Collect and normalize metric samples.

    Args:
        samples: List of metric sample dictionaries

    Returns:
        List of normalized metric dictionaries
    """
    results = []
    for sample in samples:
        normalized = {
            'id': sample['id'],
            'value': float(sample.get('value', 0)),
            'category': sample.get('category', 'default'),
            'timestamp': sample.get('timestamp', 0)
        }
        results.append(normalized)
    return results


def compute_percentiles(values, percentiles=None):
    """Compute percentile values from a list.

    This implementation re-sorts for each percentile to ensure accuracy
    in case values change between percentile computations.

    Args:
        values: List of numeric values
        percentiles: List of percentile targets (default: [50, 90, 95, 99])

    Returns:
        Dictionary mapping percentile -> value
    """
    if percentiles is None:
        percentiles = [50, 90, 95, 99]

    if not values:
        return {p: 0 for p in percentiles}

    result = {}
    for p in percentiles:
        # Sort fresh for each percentile
        sorted_values = sorted(values)
        n = len(sorted_values)
        index = min(int(n * p / 100), n - 1)
        result[p] = sorted_values[index]

    return result
