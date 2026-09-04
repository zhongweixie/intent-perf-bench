#!/usr/bin/env bash
# 新任务对比实验：fuzzy_context vs misleading（各跑3次）
# 用法：bash run_new_tasks_eval.sh
# 或在 Claude 里：! bash run_new_tasks_eval.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MODEL="claude-haiku-4-5-20251001"
RUNS=3

TASKS=(ipb_dev_015 ipb_dev_016 ipb_dev_026 ipb_dev_027 ipb_dev_033)
VARIANTS=(fuzzy_context misleading)

echo "================================================================"
echo " IPB 新任务评测：fuzzy_context vs misleading"
echo " 模型: $MODEL  |  每组: ${RUNS} 次"
echo "================================================================"

total=0; passed=0; failed=0

for task in "${TASKS[@]}"; do
    for variant in "${VARIANTS[@]}"; do
        # 跳过已有 fuzzy_context 的两个已完成任务（避免重复跑）
        if [[ "$task" == "ipb_dev_026" && "$variant" == "fuzzy_context" ]]; then
            echo "  [skip] $task/$variant — 已有结果 (demo_run1)"
            continue
        fi
        if [[ "$task" == "ipb_dev_033" && "$variant" == "fuzzy_context" ]]; then
            echo "  [skip] $task/$variant — 已有结果 (demo_run2)"
            continue
        fi

        echo ""
        echo "------------------------------------------------------------"
        echo "  任务: $task  |  变体: $variant"
        echo "------------------------------------------------------------"

        for i in $(seq 1 $RUNS); do
            run_id="new_${variant:0:4}_r${i}"
            echo "  run $i/$RUNS..."
            python3 "$SCRIPT_DIR/scripts/run_agent.py" \
                --task-id "$task" \
                --variant "$variant" \
                --model "$MODEL" \
                --max-turns 20 \
                --run-id "$run_id" 2>&1 | grep -E "passed:|✓|✗|ERROR" || true
            total=$((total+1))
        done
    done
done

echo ""
echo "================================================================"
echo "  完成。结果在 results/ 目录"
echo "  分析：python3 scripts/analyze_new_tasks.py"
echo "================================================================"
