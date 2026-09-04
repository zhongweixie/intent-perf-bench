#!/bin/bash
#
# Setup missing components for IPB tasks
#

set -e

TASKS=(
    "ipb_cuda_001"
    "ipb_cuda_002"
    "ipb_cuda_003"
    "ipb_cuda_004"
    "ipb_cuda_005_l2norm_reduction"
)

BASE_DIR="/aifs4su/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/tasks"
TEMPLATE_DIR="/aifs4su/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/templates"

echo "Setting up IPB tasks..."
echo ""

for task in "${TASKS[@]}"; do
    echo "Processing $task..."
    TASK_DIR="$BASE_DIR/$task"

    if [ ! -d "$TASK_DIR" ]; then
        echo "  ✗ Task directory does not exist: $TASK_DIR"
        continue
    fi

    cd "$TASK_DIR"

    # Create benchmarks directory
    if [ ! -d "benchmarks" ]; then
        echo "  Creating benchmarks/"
        mkdir -p benchmarks
    fi

    # Copy bench.sh template if it doesn't exist
    if [ ! -f "benchmarks/bench.sh" ]; then
        echo "  Copying bench.sh template"
        cp "$TEMPLATE_DIR/bench.sh" benchmarks/bench.sh
        chmod +x benchmarks/bench.sh
    else
        echo "  ✓ benchmarks/bench.sh exists"
    fi

    # Create variants directory
    if [ ! -d "variants" ]; then
        echo "  Creating variants/"
        mkdir -p variants
    fi

    # Create placeholder variant files if they don't exist
    if [ ! -f "variants/fuzzy.md" ]; then
        echo "  Creating variants/fuzzy.md placeholder"
        cat > variants/fuzzy.md << 'EOF'
# Fuzzy Variant

(To be completed: A less specific description of the performance issue)

## Symptom
Performance is slower than expected.

## Investigation Hints
- Check memory access patterns
- Look for synchronization overhead
- Profile kernel execution

EOF
    else
        echo "  ✓ variants/fuzzy.md exists"
    fi

    if [ ! -f "variants/misleading.md" ]; then
        echo "  Creating variants/misleading.md placeholder"
        cat > variants/misleading.md << 'EOF'
# Misleading Variant

(To be completed: A description that points in the wrong direction)

## Reported Issue
The kernel seems to have incorrect parameters.

## Misleading Hints
- Try increasing block size
- Consider using more threads
- Check if shared memory is sufficient

EOF
    else
        echo "  ✓ variants/misleading.md exists"
    fi

    echo "  ✓ $task setup complete"
    echo ""
done

echo "All tasks processed!"
echo ""
echo "Next steps:"
echo "1. Run validate_tasks.py to check status"
echo "2. Fill in variant descriptions based on each task's characteristics"
echo "3. Test benchmarks with: cd tasks/<task>/benchmarks && ./bench.sh"
