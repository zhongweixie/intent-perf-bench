#!/bin/bash
#SBATCH --job-name=ipb-eval
#SBATCH --partition=llm-debug
#SBATCH --qos=llm_debug
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --time=0-02:00:00
#SBATCH --output=/home/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/slurm_outputs/eval_%j.log
#SBATCH --error=/home/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/slurm_outputs/eval_%j.err

set -e

# ── Environment ──────────────────────────────────────────────────────────────
PYTHON=/aifs4su/hansirui_3rd/gaoyisen/miniconda3/bin/python3
WORK_DIR=/aifs4su/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench
cd $WORK_DIR

# Load CUDA module
module load cuda/12.5

echo "=========================================="
echo "IPB Evaluation on GPU Node"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURMD_NODENAME"
echo "GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)"
echo "=========================================="
echo

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
MODEL="gpt-5.6-luna"
MAX_TURNS=15

# 任务列表
TASKS=(
    "ipb_cuda_007_kmeans_clustering"
    "ipb_cuda_008_conv1d_shared"
)

VARIANTS=("fuzzy" "misleading")

for task in "${TASKS[@]}"; do
    for variant in "${VARIANTS[@]}"; do
        run_id="${task}_${variant}_${TIMESTAMP}"

        echo "=== Running: $task / $variant ==="
        echo "Run ID: $run_id"

        $PYTHON scripts/run_agent.py \
            --task-id "$task" \
            --variant "$variant" \
            --model "$MODEL" \
            --provider openai \
            --max-turns $MAX_TURNS \
            --run-id "$run_id"

        echo
        echo "✓ Completed: $task / $variant"
        echo
        sleep 5
    done
done

echo "=========================================="
echo "All evaluations complete!"
echo "=========================================="
echo

# Summary
$PYTHON << 'PYEOF'
import json
import glob
import sys

results = []
for f in glob.glob("results/*.json"):
    with open(f) as fp:
        d = json.load(fp)
        # Filter recent results
        if "20260823" in d.get("run_id", ""):
            results.append({
                "task": d["task_id"],
                "variant": d["variant"],
                "passed": d["passed"],
                "score": d.get("improvement_score"),
                "time_ms": d.get("elapsed_time"),
                "turns": d.get("turns", "?")
            })

if not results:
    print("No results found")
    sys.exit(0)

print("\nTask                              | Variant     | Passed | Score | Time(ms) | Turns")
print("-" * 95)
for r in sorted(results, key=lambda x: (x["task"], x["variant"])):
    score_str = f"{r['score']:.3f}" if r['score'] is not None else "N/A"
    time_str = f"{r['time_ms']:.0f}" if r['time_ms'] is not None else "N/A"
    print(f"{r['task']:33} | {r['variant']:11} | {str(r['passed']):6} | {score_str:5} | {time_str:>8} | {r['turns']}")

# Calculate Gap if we have fuzzy and misleading for same task
from collections import defaultdict
by_task = defaultdict(dict)
for r in results:
    if r['score'] is not None:
        by_task[r['task']][r['variant']] = r['score']

print("\n=== Gap Analysis (fuzzy - misleading) ===")
for task, scores in sorted(by_task.items()):
    if 'fuzzy' in scores and 'misleading' in scores:
        gap = scores['fuzzy'] - scores['misleading']
        print(f"{task}: fuzzy={scores['fuzzy']:.3f}, misleading={scores['misleading']:.3f}, Gap={gap:+.3f}")
PYEOF
