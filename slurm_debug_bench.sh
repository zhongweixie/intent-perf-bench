#!/bin/bash
#SBATCH --job-name=ipb-debug-bench
#SBATCH --partition=llm-debug
#SBATCH --qos=llm_debug
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=0-00:10:00
#SBATCH --output=/home/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/slurm_outputs/debug_bench_%j.log
#SBATCH --error=/home/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/slurm_outputs/debug_bench_%j.err

set -x

WORK_DIR=/aifs4su/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench
cd $WORK_DIR

module load cuda/12.5

echo "=========================================="
echo "Debug Benchmark Script"
echo "=========================================="

cd tasks/ipb_cuda_007_kmeans_clustering

echo "=== Current directory ==="
pwd
ls -la

echo
echo "=== Benchmark script content ==="
cat benchmarks/bench.sh

echo
echo "=== Run benchmark script with bash -x ==="
bash -x benchmarks/bench.sh

echo
echo "=== Check exit code ==="
echo "Exit code: $?"
