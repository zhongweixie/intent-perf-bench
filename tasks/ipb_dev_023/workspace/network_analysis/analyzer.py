"""Graph analysis algorithms."""

import json


def load_graph_data(filepath):
    """Load graph data from JSON file.

    Args:
        filepath: Path to graph JSON file

    Returns:
        Dictionary with 'nodes' and 'edges' keys
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def compute_node_degrees(graph):
    """Compute degree (number of connections) for each node.

    Uses efficient dictionary accumulation.

    Args:
        graph: Dictionary with 'nodes' and 'edges'

    Returns:
        Dictionary mapping node_id -> degree count
    """
    degrees = {node['id']: 0 for node in graph['nodes']}

    for edge in graph['edges']:
        degrees[edge['source']] += 1
        degrees[edge['target']] += 1

    return degrees


def find_connected_components(graph):
    """Find connected components using recursive DFS.

    Args:
        graph: Dictionary with 'nodes' and 'edges'

    Returns:
        List of component sets, each containing node IDs
    """
    # Build adjacency list - using list for each neighbor set
    adjacency = {node['id']: [] for node in graph['nodes']}
    for edge in graph['edges']:
        adjacency[edge['source']].append(edge['target'])
        adjacency[edge['target']].append(edge['source'])

    visited = set()
    components = []

    def dfs_recursive(node_id, component):
        """Recursive depth-first search to explore component."""
        visited.add(node_id)
        component.add(node_id)
        for neighbor in adjacency[node_id]:
            if neighbor not in visited:
                dfs_recursive(neighbor, component)

    for node in graph['nodes']:
        node_id = node['id']
        if node_id not in visited:
            component = set()
            dfs_recursive(node_id, component)
            components.append(component)

    return components
