#!/bin/bash

# Check completeness of IPB tasks

TASKS=(
    "ipb_cuda_001"
    "ipb_cuda_002"
    "ipb_cuda_003"
    "ipb_cuda_004"
    "ipb_cuda_005_l2norm_reduction"
)

echo "=== IPB Task Completeness Check ==="
echo ""

for task in "${TASKS[@]}"; do
    echo "Task: $task"
    echo "----------------------------------------"

    cd "/aifs4su/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/tasks/$task"

    # Check required files
    echo "Required files:"
    for file in task.toml workspace benchmarks/bench.sh; do
        if [ -e "$file" ]; then
            echo "  ✓ $file"
        else
            echo "  ✗ $file (MISSING)"
        fi
    done

    # Check workspace structure
    if [ -d workspace ]; then
        echo "Workspace contents:"
        ls workspace | head -10 | sed 's/^/  /'

        # Check git setup
        if [ -d workspace/.git ]; then
            cd workspace
            echo "Git commits:"
            git log --oneline | head -5 | sed 's/^/  /'
            cd ..
        else
            echo "  ✗ No git repository"
        fi
    fi

    echo ""
done
