#!/bin/bash
set -e

# Load CUDA module
module load cuda/12.2

make clean
make

# Run benchmark on GPU node
srun -p llm-debug --qos=llm_debug --gres=gpu:1 -t 5 ./layernorm_test --benchmark
