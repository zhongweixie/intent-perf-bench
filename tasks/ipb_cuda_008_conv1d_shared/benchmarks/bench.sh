#!/bin/bash
# Benchmark script for 1D Convolution task

set -e

cd "$(dirname "$0")/../workspace"

module load cuda/12.2 2>/dev/null || true
make clean >/dev/null 2>&1
make >/dev/null 2>&1

# Verify correctness first
srun -p llm-debug --qos=llm_debug --gres=gpu:1 -t 5 ./conv1d_test >/dev/null 2>&1 || {
    echo "result=correctness_fail time_ms=999999.0"
    exit 1
}

# Run performance benchmark
srun -p llm-debug --qos=llm_debug --gres=gpu:1 -t 60 ./conv1d_test --perf
