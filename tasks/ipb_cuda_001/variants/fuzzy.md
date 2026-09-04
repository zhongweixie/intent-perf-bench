# Task Description

Our model checkpoint compression system uses a canonical Huffman decoder on CUDA to decompress batches of model weights in parallel. This is critical for fast model loading during distributed training initialization.

The decoder has experienced a significant performance regression, impacting training job startup time. The decoder processes batches of compressed streams in parallel, reconstructing canonical decode tables and walking bitstreams to emit decoded bytes.

## Current Situation

- **Baseline performance** (commit `7668799`): ~5.7ms for K=2048 streams, 65536 bytes per stream
- **Current performance** (HEAD): ~124ms for the same workload
- **Threshold**: 30ms (performance must be ≤30ms to pass)

The regression occurred after a recent refactoring. The current implementation is correct (all tests pass) but unacceptably slow, causing distributed training jobs to spend excessive time in the model loading phase.

Context: When initializing a distributed training job with hundreds of GPUs, each GPU needs to quickly decompress its shard of model weights. Fast decompression directly impacts time-to-first-iteration.

## Your Task

Fix the performance regression in the CUDA decoder. The implementation must:
1. Pass correctness tests (`./huffman_decode --verify`)
2. Run in ≤30ms on the benchmark (`./huffman_decode --benchmark`)

## Build & Test

```bash
module load cuda/12.2
make clean && make
srun -p debug --gres=gpu:1 ./huffman_decode --verify    # must pass
srun -p debug --gres=gpu:1 ./huffman_decode --benchmark  # must show time_ms ≤ 30.0
```

## Files

- `solve.h` — interface (DO NOT MODIFY)
- `solve.cu` — decoder implementation (EDIT THIS)
- `stream_manager.cu` — memory management utilities (EDIT IF NEEDED)
- `main.cu` — test harness (DO NOT MODIFY)

Focus on algorithmic-level changes that restore performance without breaking correctness.
