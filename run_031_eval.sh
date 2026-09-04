#!/bin/bash
set -e
cd /aifs4su/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench

source /home/hansirui_3rd/zxiebk/scripts/claw/claw-adapters/train/rl/load_secrets.sh 2>/dev/null || true

echo "=== ipb_dev_031: fuzzy (3 runs) ==="
for i in 1 2 3; do
    echo "--- fuzzy run $i ---"
    python3 scripts/run_agent.py --task-id ipb_dev_031 --variant fuzzy 2>&1 | tail -8
done

echo ""
echo "=== ipb_dev_031: misleading (3 runs) ==="
for i in 1 2 3; do
    echo "--- misleading run $i ---"
    python3 scripts/run_agent.py --task-id ipb_dev_031 --variant misleading 2>&1 | tail -8
done

echo ""
echo "=== 结果汇总 ==="
ls -t results/ipb_dev_031_*.json | head -6 | while read f; do
    echo -n "$f: "
    python3 -c "import json; d=json.load(open('$f')); print(d.get('benchmark_pass', '?'), '|', d.get('variant','?'))"
done
