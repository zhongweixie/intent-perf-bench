#!/bin/bash
# Benchmark script for CUDA ICP task.
# Returns: result=ok time_ms=<float> (median of 7 trials)

set -e
cd "$(dirname "$0")/.."

module load cuda/12.2 2>/dev/null || true
make clean >/dev/null 2>&1
make >/dev/null 2>&1

srun -p llm-debug --qos=llm_debug --gres=gpu:1 -t 5 ./icp_corr --verify >/dev/null 2>&1 || {
    echo "result=correctness_fail time_ms=999999.0"
    exit 1
}

srun -p llm-debug --qos=llm_debug --gres=gpu:1 -t 60 ./icp_corr --benchmark
