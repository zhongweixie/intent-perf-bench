#!/bin/bash
# 运行 IPB 评测：对比 fuzzy vs misleading 变体

PYTHON=/aifs4su/hansirui_3rd/gaoyisen/miniconda3/bin/python3
WORK_DIR=/aifs4su/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench
cd $WORK_DIR

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
MODEL="gpt-5.6-luna"
MAX_TURNS=15

# 任务列表
TASKS=(
    "ipb_cuda_007_kmeans_clustering"
    "ipb_cuda_008_conv1d_shared"
)

VARIANTS=("fuzzy" "misleading")

echo "=========================================="
echo "IPB Evaluation: fuzzy vs misleading"
echo "Model: $MODEL"
echo "Tasks: ${TASKS[@]}"
echo "Timestamp: $TIMESTAMP"
echo "=========================================="
echo

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
            --run-id "$run_id" 2>&1 | tee "results/logs/${run_id}.log"

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
echo "=== Summary ==="
$PYTHON << 'PYEOF'
import json
import glob

results = []
for f in glob.glob("results/*.json"):
    if "20260823" in f or "kmeans" in f or "conv1d" in f:
        with open(f) as fp:
            d = json.load(fp)
            results.append({
                "task": d["task_id"],
                "variant": d["variant"],
                "score": d["improvement_score"],
                "time_ms": d["elapsed_time"],
                "turns": d.get("turn_count", "?")
            })

print("\nTask                              | Variant     | Score | Time(ms) | Turns")
print("-" * 85)
for r in sorted(results, key=lambda x: (x["task"], x["variant"])):
    print(f"{r['task']:33} | {r['variant']:11} | {r['score']:.3f} | {r['time_ms']:8.0f} | {r['turns']}")
PYEOF
