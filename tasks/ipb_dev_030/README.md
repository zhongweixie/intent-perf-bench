# ipb_dev_030: Event Aggregate Per-Type Scan

## Overview

Performance benchmark task testing agent ability to diagnose and fix repeated full-scan aggregation where a single-pass dict accumulation would suffice.

## Problem Description

The event processing pipeline has regressed from ~0.11s to ~0.16s (1.5x slowdown). The bottleneck is in `event_processor/processor.py` where `aggregate_by_type()` scans all 100k events once per event type (10 scans total) instead of accumulating in a single pass.

## Workspace Structure

```
workspace/
├── event_processor/
│   ├── __init__.py
│   └── processor.py        # PERFORMANCE BOTTLENECK HERE
├── benchmarks/
│   └── event_bench.py      # Performance test (threshold: 0.15s)
├── run_pipeline.py         # Interactive pipeline runner
├── generate_data.py        # Test data generation
├── test_events.json        # 100k events
└── profiling_data.txt      # cProfile evidence (variant: exact_evidence)
```

## Ground Truth

**Bottleneck**: `aggregate_by_type()` filters all events per type

**Root Cause**: For each of 10 types, the function scans all 100k events with list comprehension = 1M total iterations instead of 100k.

**Solution**: Single-pass dict accumulation
```python
aggregates = {}
for event in events:
    event_type = event['type']
    if event_type not in aggregates:
        aggregates[event_type] = {'count': 0, 'total_duration': 0}
    aggregates[event_type]['count'] += 1
    aggregates[event_type]['total_duration'] += event['duration_ms']
for stats in aggregates.values():
    stats['avg_duration'] = stats['total_duration'] / stats['count']
```

## Git History

- Commit 1 (baseline): Single-pass dict accumulation - FAST
- Commit 2 (regression): "refactor: per-type event filtering for explicit processing" - SLOW
- Commit 3: Add profiling evidence
