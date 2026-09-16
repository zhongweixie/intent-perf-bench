#!/usr/bin/env python3
"""Generate test graph data for network analysis."""

import json
import random


def generate_graph_data(num_nodes=1000, avg_edges_per_node=5):
    """Generate graph data with nodes and edges.

    Args:
        num_nodes: Number of nodes in the graph
        avg_edges_per_node: Average number of edges per node

    Returns:
        Dictionary with nodes and edges
    """
    nodes = []
    edges = []

    # Generate nodes with properties
    for i in range(num_nodes):
        node = {
            'id': f"node_{i:04d}",
            'label': f"Node {i}",
            'weight': random.randint(1, 100),
            'category': random.choice(['A', 'B', 'C', 'D'])
        }
        nodes.append(node)

    # Generate edges
    num_edges = num_nodes * avg_edges_per_node // 2
    node_ids = [n['id'] for n in nodes]

    for _ in range(num_edges):
        source = random.choice(node_ids)
        target = random.choice(node_ids)
        if source != target:
            edge = {
                'source': source,
                'target': target,
                'weight': random.uniform(0.1, 10.0)
            }
            edges.append(edge)

    return {'nodes': nodes, 'edges': edges}


if __name__ == '__main__':
    print("Generating graph data...")
    graph = generate_graph_data(num_nodes=5000, avg_edges_per_node=5)

    with open('graph_data.json', 'w', encoding='utf-8') as f:
        json.dump(graph, f, indent=2)

    print(f"Generated {len(graph['nodes'])} nodes, {len(graph['edges'])} edges -> graph_data.json")
