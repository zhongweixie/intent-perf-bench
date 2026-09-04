#!/bin/bash
# CUDA IPB 任务批量评测脚本
# 用法：
#   ./run_cuda_eval.sh [provider] [model]
# 示例：
#   ./run_cuda_eval.sh openai gpt-5.6-luna
#   ./run_cuda_eval.sh anthropic claude-opus-5

set -e

PROVIDER=${1:-openai}
MODEL=${2:-gpt-5.6-luna}
MAX_TURNS=25
RUNS_PER_VARIANT=5

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
cd "$SCRIPT_DIR/.."

echo "==================================="
echo "CUDA IPB 批量评测"
echo "Provider: $PROVIDER"
echo "Model: $MODEL"
echo "Runs per variant: $RUNS_PER_VARIANT"
echo "==================================="
echo

TASKS=(ipb_cuda_001 ipb_cuda_002 ipb_cuda_003)
VARIANTS=(fuzzy misleading)

for task in "${TASKS[@]}"; do
    for variant in "${VARIANTS[@]}"; do
        echo "--- $task / $variant ---"
        for i in $(seq 1 $RUNS_PER_VARIANT); do
            run_id="run${i}_$(date +%s)"
            echo "  Run $i/5 (${run_id})..."
            python scripts/run_agent.py \
                --task-id "$task" \
                --variant "$variant" \
                --provider "$PROVIDER" \
                --model "$MODEL" \
                --max-turns "$MAX_TURNS" \
                --run-id "$run_id" 2>&1 | tail -20
            echo
        done
    done
done

echo "==================================="
echo "评测完成！结果位于 results/"
echo "==================================="
