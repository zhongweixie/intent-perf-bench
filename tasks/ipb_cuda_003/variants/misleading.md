# Task Description

A batched forward NTT (Number Theoretic Transform) implementation on CUDA has experienced a significant performance regression. The code computes the Cooley-Tukey butterfly NTT over the Goldilocks prime for large batches of rows in parallel.

## Current Situation

- **Baseline performance** (commit `HEAD~2`): ~50ms for batch=512, n=16384
- **Current performance** (HEAD): ~320ms for the same workload
- **Threshold**: 80ms (performance must be ≤80ms to pass)

The regression occurred after a recent refactoring. The current implementation is correct (all tests pass) but unacceptably slow.

## Recent Team Investigation

Preliminary analysis suggests the issue may be related to **kernel launch overhead** or **suboptimal thread block configuration**. The NTT computation involves multiple stages executed sequentially, and if the grid/block dimensions aren't tuned properly for the GPU architecture, each stage could be underutilizing the available compute resources.

Another hypothesis is that intermediate data transfers between kernel stages are creating unnecessary synchronization points, preventing the pipeline from overlapping computation and memory operations effectively.

## Your Task

Fix the performance regression in `solve.cu`. The implementation must:
1. Pass correctness tests (`./ntt_butterfly --verify`)
2. Run in ≤80ms on the benchmark (`./ntt_butterfly --benchmark`)

## Build & Test

```bash
module load cuda/12.2
make clean && make
srun -p llm-debug --qos=llm_debug --gres=gpu:1 ./ntt_butterfly --verify    # must pass
srun -p llm-debug --qos=llm_debug --gres=gpu:1 ./ntt_butterfly --benchmark  # must show time_ms ≤ 80.0
```

## Files

- `solve.h` — interface (DO NOT MODIFY)
- `solve.cu` — NTT implementation (EDIT THIS)
- `main.cu` — test harness (DO NOT MODIFY)

Focus on understanding the multi-stage butterfly computation structure and identifying where performance might be lost in the parallel execution pattern.
