#!/bin/bash
#SBATCH --job-name=ipb-benchmark
#SBATCH --partition=llm-debug
#SBATCH --qos=llm_debug
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --time=0-01:00:00
#SBATCH --output=/home/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/slurm_outputs/benchmark_%j.log
#SBATCH --error=/home/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/slurm_outputs/benchmark_%j.err

# ── Environment ──────────────────────────────────────────────────────────────
WORK_DIR=/aifs4su/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench
cd $WORK_DIR

# Load CUDA module
module load cuda/12.5

# ── Benchmark Task Performance ──────────────────────────────────────────────
echo "=========================================="
echo "IPB Benchmark Performance Testing"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURMD_NODENAME"
echo "GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)"
echo "=========================================="
echo

# Function to benchmark a task
benchmark_task() {
    local task_id=$1
    local task_name=$2

    echo "=== Benchmarking $task_name ($task_id) ==="
    echo

    cd $WORK_DIR/tasks/$task_id/workspace

    # Checkout baseline
    echo "Testing baseline (slow version)..."
    git checkout ipb-baseline 2>/dev/null

    if [ -f "Makefile" ]; then
        # CUDA C++ tasks
        make clean
        make

        # Find the test executable
        test_exec=$(ls *_test 2>/dev/null | head -1)
        if [ -z "$test_exec" ]; then
            echo "Error: No test executable found"
            return 1
        fi

        # Run benchmark multiple times and average
        echo "Running baseline benchmark (3 runs) with ./$test_exec --perf..."
        for i in 1 2 3; do
            echo "  Run $i:"
            timeout 60 ./$test_exec --perf 2>&1 | tail -20
        done
    elif [ -f "solution.py" ]; then
        # Python cuTile tasks
        echo "Running baseline benchmark (3 runs)..."
        for i in 1 2 3; do
            echo "  Run $i:"
            timeout 60 python3 test/test_fmha.py --perf 2>&1 | tail -20
        done
    fi

    echo

    # Checkout reference
    echo "Testing reference (optimized version)..."
    git checkout ipb-reference 2>/dev/null

    if [ -f "Makefile" ]; then
        make clean
        make

        test_exec=$(ls *_test 2>/dev/null | head -1)
        if [ -z "$test_exec" ]; then
            echo "Error: No test executable found"
            return 1
        fi

        echo "Running optimized benchmark (3 runs) with ./$test_exec --perf..."
        for i in 1 2 3; do
            echo "  Run $i:"
            timeout 60 ./$test_exec --perf 2>&1 | tail -20
        done
    elif [ -f "solution.py" ]; then
        echo "Running optimized benchmark (3 runs)..."
        for i in 1 2 3; do
            echo "  Run $i:"
            timeout 60 python3 test/test_fmha.py --perf 2>&1 | tail -20
        done
    fi

    echo
    echo "=== $task_name complete ==="
    echo
}

# Create output directory
mkdir -p $WORK_DIR/slurm_outputs

# Benchmark each task
benchmark_task "ipb_cuda_007_kmeans_clustering" "K-Means Clustering"
benchmark_task "ipb_cuda_008_conv1d_shared" "1D Convolution"
# Skip Flash Attention for now (needs cuTile setup)
# benchmark_task "ipb_cuda_006_flash_attention_cutile" "Flash Attention"

echo "=========================================="
echo "All benchmarks complete!"
echo "=========================================="
