"""Results export module."""

import json


def export_results(analysis, output_path):
    """Export analysis results to JSON file.

    Args:
        analysis: Analysis results dictionary
        output_path: Path to output JSON file
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2)
