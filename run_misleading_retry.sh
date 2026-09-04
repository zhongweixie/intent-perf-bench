#!/usr/bin/env bash
# 重新测试加强后的 misleading variant（015, 026, 033）v3
# 每个任务跑 3 次 misleading
# 用法：bash /aifs4su/.../run_misleading_retry.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MODEL="claude-haiku-4-5-20251001"

TASKS=(ipb_dev_015 ipb_dev_026 ipb_dev_033)

echo "================================================================"
echo " 重新测试加强版 misleading v3（ipb_dev_015/026/033）"
echo " 误导策略：合理但不完整的修法路径（参考 ipb_dev_027）"
echo " 模型: $MODEL  |  每组: 3 次"
echo "================================================================"

for task in "${TASKS[@]}"; do
    echo ""
    echo "------------------------------------------------------------"
    echo "  任务: $task  |  变体: misleading"
    echo "------------------------------------------------------------"

    for i in 1 2 3; do
        run_id="misl_v3_r${i}"
        echo "  run $i/3..."
        python3 "$SCRIPT_DIR/scripts/run_agent.py" \
            --task-id "$task" \
            --variant misleading \
            --model "$MODEL" \
            --max-turns 20 \
            --run-id "$run_id" 2>&1 | grep -E "passed:|ERROR" || true
    done
done

echo ""
echo "================================================================"
echo "  完成。分析："
echo "  python3 scripts/analyze_new_tasks.py"
echo "================================================================"
