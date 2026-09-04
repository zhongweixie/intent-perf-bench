#!/bin/bash
#SBATCH --job-name=test-bench-fix
#SBATCH --partition=llm-debug
#SBATCH --qos=llm_debug
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=0-00:10:00
#SBATCH --output=/home/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/slurm_outputs/test_bench_fix_%j.log
#SBATCH --error=/home/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/slurm_outputs/test_bench_fix_%j.err

set -ex

WORK_DIR=/aifs4su/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench
cd $WORK_DIR

module load cuda/12.5

echo "=========================================="
echo "Test Fixed Benchmark Scripts"
echo "=========================================="

cd tasks/ipb_cuda_007_kmeans_clustering

echo "=== Show bench.sh content ==="
cat benchmarks/bench.sh

echo
echo "=== Run bench.sh from task root ==="
bash benchmarks/bench.sh

echo
echo "=== Exit code: $? ==="
