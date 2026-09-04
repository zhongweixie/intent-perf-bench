#!/usr/bin/env bash
# 测试 ipb_dev_034（新设计的有效 misleading 任务）
# fuzzy_context × 3 + misleading × 3
# 用法：bash /aifs4su/.../run_034_eval.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MODEL="claude-haiku-4-5-20251001"

echo "================================================================"
echo " ipb_dev_034 评测：fuzzy_context vs misleading"
echo " 结构同 ipb_dev_027（re 预编译有效但不够，isdigit 才是正解）"
echo " 模型: $MODEL  |  每组: 3 次"
echo "================================================================"

for variant in fuzzy_context misleading; do
    echo ""
    echo "------------------------------------------------------------"
    echo "  任务: ipb_dev_034  |  变体: $variant"
    echo "------------------------------------------------------------"

    for i in 1 2 3; do
        run_id="034_${variant:0:4}_r${i}"
        echo "  run $i/3..."
        python3 "$SCRIPT_DIR/scripts/run_agent.py" \
            --task-id ipb_dev_034 \
            --variant "$variant" \
            --model "$MODEL" \
            --max-turns 20 \
            --run-id "$run_id" 2>&1 | grep -E "passed:|ERROR" || true
    done
done

echo ""
echo "================================================================"
echo "  完成。分析："
echo "  python3 scripts/analyze_034.py"
echo "================================================================"
