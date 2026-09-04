# Task Description

A BLS12-381 G1 Multi-Scalar Multiplication (MSM) implementation has experienced a significant performance regression. The code computes `Q = sum_i s_i * P_i` over the BLS12-381 G1 elliptic curve using the Pippenger algorithm.

## Current Situation

- **Baseline performance** (commit `HEAD~1`): ~59ms for N=262144 points
- **Current performance** (HEAD): ~624ms for the same workload
- **Threshold**: 200ms (performance must be ≤200ms to pass)

The regression occurred after a recent refactoring. The current implementation is correct (all tests pass) but unacceptably slow.

## Your Task

Fix the performance regression in `solve.cu`. The implementation must:
1. Pass correctness tests (`./msm_bls12381 --verify`)
2. Run in ≤200ms on the benchmark (`./msm_bls12381 --benchmark`)

## Build & Test

```bash
export PATH=/home/hansirui_3rd/cuda-12/bin:$PATH
make clean && make
srun -p llm-debug --qos=llm_debug --gres=gpu:1 ./msm_bls12381 --verify    # must pass
srun -p llm-debug --qos=llm_debug --gres=gpu:1 ./msm_bls12381 --benchmark  # must show median_ms ≤ 200.0
```

## Files

- `solve.h` — interface and data structures (DO NOT MODIFY)
- `solve.cu` — MSM implementation (EDIT THIS)
- `main.cu` — test harness (DO NOT MODIFY)

Focus on the bucket accumulation phase. The Pippenger algorithm decomposes scalars into windows and accumulates points into per-window buckets — understanding this structure is key to finding the regression.
