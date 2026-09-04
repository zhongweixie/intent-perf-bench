# ipb_dev_023: Graph DFS Recursion Depth Error

## Overview

Performance benchmark task testing agent ability to diagnose and fix a RecursionError caused by recursive DFS implementation on large graphs.

## Problem Description

The network analysis pipeline crashes with `RecursionError: maximum recursion depth exceeded` when processing graphs with 5000+ nodes. The issue is in `network_analysis/analyzer.py` where recursive DFS hits Python's default recursion limit (~1000).

## Workspace Structure

```
workspace/
├── network_analysis/
│   ├── __init__.py
│   └── analyzer.py        # RECURSION ERROR HERE
├── benchmarks/
│   └── network_bench.py   # Crashes on large graphs
├── run_pipeline.py        # Interactive pipeline runner
├── generate_data.py       # Graph data generation
├── graph_data.json        # 5000 nodes, ~12k edges
└── profiling_data.txt     # cProfile evidence (variant: exact_evidence)
```

## Test Variants

### 1. exact_evidence
- Provides profiling data showing recursive call patterns
- System prompt explicitly mentions error traces and available evidence
- Tests agent's ability to interpret stack traces and apply fix

### 2. fuzzy_context
- Minimal context: "pipeline crashes on large graphs"
- No profiling data or traces provided upfront
- Tests agent's investigation and diagnosis capabilities

## Ground Truth

**Bottleneck**: `find_connected_components()` uses recursive DFS

**Root Cause**: Recursive calls accumulate on call stack, exceeding Python's limit (~1000) for large connected components

**Solution**: Iterative DFS with explicit stack
```python
def find_connected_components(graph):
    # Build adjacency list
    adjacency = {node['id']: set() for node in graph['nodes']}
    for edge in graph['edges']:
        adjacency[edge['source']].add(edge['target'])
        adjacency[edge['target']].add(edge['source'])
    
    visited = set()
    components = []
    
    for node in graph['nodes']:
        node_id = node['id']
        if node_id not in visited:
            # Iterative DFS with explicit stack
            component = set()
            stack = [node_id]
            
            while stack:
                current = stack.pop()
                if current in visited:
                    continue
                visited.add(current)
                component.add(current)
                for neighbor in adjacency[current]:
                    if neighbor not in visited:
                        stack.append(neighbor)
            
            components.append(component)
    
    return components
```

**Expected Outcome**: No RecursionError, benchmark passes, same component results

## Evaluation Criteria

1. **Correctness**: `python3 benchmarks/network_bench.py` exits 0 (no crash)
2. **Results Unchanged**: Same number of components and same node membership
3. **Code Quality**: Fix addresses recursion limit, not symptoms (e.g., don't just increase recursion limit)

## Git History

- Commit 1 (baseline): Iterative DFS with explicit visited check - WORKS
- Commit 2: Increase graph size to 5000 nodes
- Commit 3 (regression): "refactor: switch to recursive DFS for cleaner code structure" - CRASHES

The regression commit message is misleading (claims "cleaner code" but introduces crash).

## Running Tests

```bash
cd tasks/ipb_dev_023/workspace

# Interactive pipeline (will crash)
python3 run_pipeline.py

# Performance benchmark (will crash)
python3 benchmarks/network_bench.py
```

## Success Indicators

Agent should:
1. Identify `analyzer.py` as crash location (via stack trace or error messages)
2. Recognize recursive DFS as root cause
3. Refactor to iterative DFS with explicit stack
4. Validate with benchmark showing no crash and best_time ≤ 0.12s
5. Verify correctness (same component results)

## Notes

- RecursionError clearly indicates the problem (unlike subtle performance regressions)
- Git log provides narrative clue: recent "refactor" introduced the crash
- Simply increasing `sys.setrecursionlimit()` is NOT a proper fix (anti-pattern)
- The misleading commit message tests whether agent validates claims vs actual behavior
