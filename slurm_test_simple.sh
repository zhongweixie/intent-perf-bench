#!/bin/bash
#SBATCH --job-name=ipb-test
#SBATCH --partition=llm-debug
#SBATCH --qos=llm_debug
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=0-00:10:00
#SBATCH --output=/home/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/slurm_outputs/test_%j.log
#SBATCH --error=/home/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/slurm_outputs/test_%j.err

set -x  # 显示所有执行的命令

# ── Environment ──────────────────────────────────────────────────────────────
WORK_DIR=/aifs4su/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench
cd $WORK_DIR

# Load CUDA module
module load cuda/12.5

echo "=========================================="
echo "IPB Simple Test"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURMD_NODENAME"
echo "=========================================="

# Test GPU access
echo "=== GPU Info ==="
nvidia-smi

echo
echo "=== Test K-Means Baseline ==="
cd $WORK_DIR/tasks/ipb_cuda_007_kmeans_clustering/workspace

git checkout ipb-baseline
make clean
make

echo
echo "=== Run baseline (correctness test, not --perf) ==="
timeout 30 ./kmeans_test

echo
echo "=== Run baseline performance test ==="
timeout 30 ./kmeans_test --perf

echo
echo "=========================================="
echo "Test complete!"
echo "=========================================="
