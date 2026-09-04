#!/bin/bash
#SBATCH --job-name=ipb-perf
#SBATCH --partition=llm-debug
#SBATCH --qos=llm_debug
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=0-00:30:00
#SBATCH --output=/home/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/slurm_outputs/perf_%j.log
#SBATCH --error=/home/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/slurm_outputs/perf_%j.err

set -e

# ── Environment ──────────────────────────────────────────────────────────────
WORK_DIR=/aifs4su/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench
cd $WORK_DIR

# Load CUDA module
module load cuda/12.5

echo "=========================================="
echo "IPB Performance Measurement"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURMD_NODENAME"
echo "GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)"
echo "=========================================="
echo

# Function to measure performance
measure_task() {
    local task_id=$1
    local task_name=$2

    echo "=== $task_name ($task_id) ==="
    cd $WORK_DIR/tasks/$task_id/workspace

    # Measure baseline
    echo "Baseline (slow version):"
    git checkout ipb-baseline 2>&1 | grep "HEAD is now"
    make clean > /dev/null 2>&1
    make > /dev/null 2>&1

    test_exec=$(ls *_test 2>/dev/null | head -1)
    baseline_json=$(./$test_exec --perf 2>&1 | grep "time_ms")
    echo "$baseline_json"
    baseline_ms=$(echo "$baseline_json" | python3 -c "import json,sys; print(json.load(sys.stdin)['time_ms'])")

    # Measure reference
    echo "Reference (optimized version):"
    git checkout ipb-reference 2>&1 | grep "HEAD is now"
    make clean > /dev/null 2>&1
    make > /dev/null 2>&1

    reference_json=$(./$test_exec --perf 2>&1 | grep "time_ms")
    echo "$reference_json"
    reference_ms=$(echo "$reference_json" | python3 -c "import json,sys; print(json.load(sys.stdin)['time_ms'])")

    # Calculate speedup
    speedup=$(python3 -c "print(f'{$baseline_ms / $reference_ms:.2f}x')")

    echo "Summary:"
    echo "  Baseline:  ${baseline_ms} ms"
    echo "  Reference: ${reference_ms} ms"
    echo "  Speedup:   $speedup"
    echo

    # Write to task.toml
    sed -i "s/regressed_ms = 0.0/regressed_ms = $baseline_ms/" $WORK_DIR/tasks/$task_id/task.toml
    sed -i "s/optimal_ms = 0.0/optimal_ms = $reference_ms/" $WORK_DIR/tasks/$task_id/task.toml

    echo "✓ Updated task.toml"
    echo
}

# Measure each task
measure_task "ipb_cuda_007_kmeans_clustering" "K-Means Clustering"
measure_task "ipb_cuda_008_conv1d_shared" "1D Convolution"

echo "=========================================="
echo "Performance measurement complete!"
echo "=========================================="
