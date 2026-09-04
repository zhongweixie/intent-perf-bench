# Task Description

An ICP (Iterative Closest Point) correspondence implementation has experienced a significant performance regression. The code finds nearest-neighbor matches between source and target point clouds on GPU.

## Current Situation

- **Baseline performance** (commit `HEAD~1`): ~65ms for N=200,000 source points, M=500,000 target points
- **Current performance** (HEAD): ~543ms for the same workload
- **Threshold**: 150ms (performance must be ≤150ms to pass)

The regression occurred after a recent refactoring. The current implementation is correct (all tests pass) but unacceptably slow.

## Your Task

Fix the performance regression in `solve.cu`. The implementation must:
1. Pass correctness tests (`./icp_corr --verify`)
2. Run in ≤150ms on the benchmark (`./icp_corr --benchmark`)

## Build & Test

```bash
make clean && make
./icp_corr --verify    # must pass
./icp_corr --benchmark # must show time_ms ≤ 150.0
```

## Files

- `solve.h` — interface (DO NOT MODIFY)
- `solve.cu` — your implementation (EDIT THIS)
- `main.cu` — test harness (DO NOT MODIFY)

Focus on algorithmic-level changes that restore performance without breaking correctness.
