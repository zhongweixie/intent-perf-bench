#!/bin/bash
#SBATCH --job-name=ipb-009-measure
#SBATCH --partition=llm-debug
#SBATCH --qos=llm_debug
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=0-00:10:00
#SBATCH --output=/home/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/slurm_outputs/measure_009_%j.log

set -ex

WORK_DIR=/aifs4su/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench
cd $WORK_DIR/tasks/ipb_cuda_009_matrix_transpose/workspace

module load cuda/12.5

echo "=========================================="
echo "Measure 009 Matrix Transpose Performance"
echo "=========================================="

echo
echo "=== Baseline (with bank conflicts) ==="
git checkout ipb-baseline
make clean
make
./transpose_test --perf

echo
echo "=== Reference (with padding) ==="
git checkout ipb-reference
make clean
make
./transpose_test --perf

echo
echo "=========================================="
echo "测量完成"
echo "=========================================="
