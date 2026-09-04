#!/bin/bash
set -e
cd "$(dirname "$0")/.."

module load cuda/12.2 2>/dev/null || true
make clean >/dev/null 2>&1
make >/dev/null 2>&1

srun -p llm-debug --qos=llm_debug --gres=gpu:1 -t 5 ./l2norm_test >/dev/null 2>&1 || {
    echo "result=correctness_fail time_ms=999999.0"
    exit 1
}

srun -p llm-debug --qos=llm_debug --gres=gpu:1 -t 60 ./l2norm_bench
