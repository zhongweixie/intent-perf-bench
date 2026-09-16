"""Order loader — reads order records from JSON."""

import os

try:
    import orjson as _json_lib
    _USE_ORJSON = True
except ImportError:
    import json as _json_lib
    _USE_ORJSON = False


def load_orders(path=None):
    """Load order records from JSON file.

    Args:
        path: Path to orders JSON file. Defaults to orders.json in workspace.

    Returns:
        List of order dictionaries.
    """
    if path is None:
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'orders.json')

    if _USE_ORJSON:
        with open(path, 'rb') as f:
            return _json_lib.loads(f.read())
    else:
        with open(path, 'r') as f:
            return _json_lib.load(f)
