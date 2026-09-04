#!/bin/bash
set -e
cd /aifs4su/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench
source /home/hansirui_3rd/zxiebk/scripts/claw/claw-adapters/train/rl/load_secrets.sh 2>/dev/null || true

echo "=== ipb_dev_035: fuzzy (3 runs) ==="
for i in 1 2 3; do
    echo "--- fuzzy run $i ---"
    python3 scripts/run_agent.py --task-id ipb_dev_035 --variant fuzzy 2>&1 | tail -4
done

echo ""
echo "=== ipb_dev_035: misleading (3 runs) ==="
for i in 1 2 3; do
    echo "--- misleading run $i ---"
    python3 scripts/run_agent.py --task-id ipb_dev_035 --variant misleading 2>&1 | tail -4
done

echo ""
echo "=== 结果汇总 ==="
python3 -c "
import json, pathlib
files = sorted(pathlib.Path('results').glob('ipb_dev_035_*.json'))
for f in files[-6:]:
    d = json.load(open(f))
    print(f'  {f.name}: passed={d.get(\"passed\")} variant={d.get(\"variant\")} turns={d.get(\"turns\")}')
"
