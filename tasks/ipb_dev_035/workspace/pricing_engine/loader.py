"""Order loader — reads order records from JSON."""

import json
import os


def load_orders(path=None):
    """Load order records from JSON file.

    Args:
        path: Path to orders JSON file. Defaults to orders.json in workspace.

    Returns:
        List of order dictionaries.
    """
    if path is None:
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'orders.json')

    with open(path, 'r') as f:
        return json.load(f)
