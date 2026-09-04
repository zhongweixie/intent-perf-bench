#!/bin/bash
#SBATCH --job-name=ipb-bench-direct
#SBATCH --partition=llm-debug
#SBATCH --qos=llm_debug
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=0-00:10:00
#SBATCH --output=/home/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/slurm_outputs/bench_direct_%j.log
#SBATCH --error=/home/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/slurm_outputs/bench_direct_%j.err

set -ex

WORK_DIR=/aifs4su/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench
cd $WORK_DIR

module load cuda/12.5

echo "=========================================="
echo "Direct Benchmark Test"
echo "=========================================="

# Test K-Means directly
cd tasks/ipb_cuda_007_kmeans_clustering/workspace

echo "=== Build K-Means ==="
git checkout ipb-baseline
make clean
make

echo
echo "=== Run K-Means benchmark ==="
./kmeans_test --perf

echo
echo "=== Exit code: $? ==="

echo
echo "=========================================="

# Test 1D Conv directly
cd $WORK_DIR/tasks/ipb_cuda_008_conv1d_shared/workspace

echo "=== Build 1D Conv ==="
git checkout ipb-baseline
make clean
make

echo
echo "=== Run 1D Conv benchmark ==="
./conv1d_test --perf

echo
echo "=== Exit code: $? ==="
