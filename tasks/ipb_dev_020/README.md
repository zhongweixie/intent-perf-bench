# ipb_dev_020: LRU Cache Eviction Missing

## Overview

Performance benchmark task testing agent ability to diagnose and fix missing LRU eviction logic in a cache system.

## Problem Description

The cache system's "simplified" refactor removed critical LRU maintenance logic. The cache now grows unbounded beyond its capacity (2000 items vs 1000 capacity limit), causing memory bloat and degraded performance over time.

## Workspace Structure

```
workspace/
├── cache_manager/
│   ├── __init__.py
│   ├── lru_cache.py        # PERFORMANCE BOTTLENECK HERE
│   └── cache_ops.py        # Global cache operations
├── benchmarks/
│   └── cache_bench.py      # Performance test (threshold: 0.015s)
├── queries.json            # 50k lookup queries
├── source_data.json        # 2k unique records
├── generate_data.py        # Test data generation
├── run_pipeline.py         # Interactive pipeline runner
└── profiling_data.txt      # Cache growth evidence (variant: exact_evidence)
```

## Test Variants

### 1. exact_evidence
- Provides profiling data showing cache size exceeding capacity (2000 > 1000)
- System prompt explicitly mentions available evidence files
- Tests agent's ability to recognize missing eviction logic

### 2. fuzzy_context
- Minimal context: "cache system has regressed"
- No profiling data provided upfront
- Tests agent's investigation and diagnosis capabilities

## Ground Truth

**Bottleneck**: `LRUCache.get()` and `set()` methods lack LRU maintenance

**Root Cause**: "Simplification" removed two critical operations:
1. `get()` no longer calls `move_to_end()` to mark items as recently used
2. `set()` no longer evicts oldest items when at capacity

```python
# Before (CORRECT):
def get(self, key):
    ...
    self.cache.move_to_end(key)  # Mark as recently used
    return self.cache[key]

def set(self, key, value):
    if key in self.cache:
        self.cache.move_to_end(key)
    elif len(self.cache) >= self.capacity:
        self.cache.popitem(last=False)  # Evict oldest
    self.cache[key] = value

# After (BROKEN):
def get(self, key):
    ...
    return self.cache[key]  # No LRU update!

def set(self, key, value):
    self.cache[key] = value  # No eviction!
```

**Solution**: Restore LRU maintenance logic
```python
def get(self, key):
    if key not in self.cache:
        self.misses += 1
        return None
    self.hits += 1
    self.cache.move_to_end(key)  # ← Restore this
    return self.cache[key]

def set(self, key, value):
    if key in self.cache:
        self.cache.move_to_end(key)  # ← Restore this
    elif len(self.cache) >= self.capacity:
        self.cache.popitem(last=False)  # ← Restore this
    self.cache[key] = value
```

**Expected Outcome**: Cache stays within capacity bounds, memory usage controlled

## Evaluation Criteria

1. **Performance**: `python3 benchmarks/cache_bench.py` exits 0 (best time ≤ 0.015s)
2. **Correctness**: Cache hit/miss rates unchanged, capacity limit enforced
3. **Code Quality**: Fix restores proper LRU semantics

## Git History

- Commit 1 (baseline): Full LRU implementation with move_to_end and eviction - CORRECT
- Commit 2 (regression): "refactor: simplify cache operations by removing LRU maintenance overhead" - BROKEN
- Commit 3: Add profiling evidence showing unbounded growth

The regression commit claims to remove "overhead" but breaks the cache invariant.

## Running Tests

```bash
cd tasks/ipb_dev_020/workspace

# Interactive pipeline with cache statistics
python3 run_pipeline.py

# Performance benchmark
PYTHONPATH=. python3 benchmarks/cache_bench.py
```

## Success Indicators

Agent should:
1. Identify `lru_cache.py` as the problem source (via profiling, git diff, or code inspection)
2. Recognize that cache grows beyond capacity (2000 > 1000)
3. Understand that LRU eviction logic is missing
4. Restore `move_to_end()` and `popitem(last=False)` operations
5. Validate with benchmark and verify cache size stays within capacity

## Notes

- Profiling shows cache size reaches 2000 (2x the capacity limit)
- The cache still functions correctly in terms of hits/misses, but memory usage is unbounded
- This is a subtle algorithmic regression: the data structure semantics are violated
- Tests agent's understanding of cache eviction policies (LRU specifically)
- "Simplification" that removes essential behavior is a common anti-pattern
- Performance degradation may manifest gradually as memory pressure increases
