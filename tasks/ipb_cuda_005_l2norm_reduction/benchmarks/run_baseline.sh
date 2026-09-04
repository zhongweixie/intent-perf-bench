#!/bin/bash

cd "$(dirname "$0")/../workspace" || exit 1

echo "=== Building baseline version ==="
make clean && make

if [ $? -ne 0 ]; then
    echo "Build failed"
    exit 1
fi

echo ""
echo "=== Running verification ==="
./l2norm_benchmark --verify

echo ""
echo "=== Running benchmark ==="
srun -p llm-debug --qos=llm_debug --gres=gpu:1 ./l2norm_benchmark --benchmark
