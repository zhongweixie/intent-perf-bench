# Performance Investigation Request

Hi! Our analytics pipeline has become slower recently and we need your help to investigate and fix it.

## What we're seeing

The benchmark is failing - it's taking around 0.86 seconds when it should be under 0.5 seconds.

## What we know

The performance regression is in the `analytics/aggregator.py` file, specifically in the `calculate_derived_metrics()` function. A recent refactoring changed how this function works.

## Evidence available

I've saved the recent benchmark output and git history in the workspace - you can examine the changes to understand what happened.

## What we need

Please fix the performance regression in `analytics/aggregator.py` so the benchmark passes.

You can run `python3 benchmarks/analytics_bench.py` to verify your fix works.

Thanks!
