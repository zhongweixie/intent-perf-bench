#!/bin/bash
# 重新标定使用 --benchmark-verify 的 CUDA 任务
# 运行：bash scripts/recalibrate_benchmark_verify_tasks.sh

set -e

TASKS=(
    "ipb_cuda_001"
    "ipb_cuda_003"
    "ipb_cuda_004"
    "ipb_cuda_005_icp_correspondence"
)

echo "=== 重新标定 --benchmark-verify 任务 ==="
echo "任务列表："
for task in "${TASKS[@]}"; do
    echo "  - $task"
done
echo ""

for task in "${TASKS[@]}"; do
    echo "=== 标定 $task ==="
    python3 scripts/calibrate_task.py --task-id "$task" --n-runs 7 --warmup 2

    if [ $? -eq 0 ]; then
        echo "✓ $task 标定完成"
    else
        echo "✗ $task 标定失败"
        exit 1
    fi
    echo ""
done

echo "=== 所有任务标定完成 ==="
echo ""
echo "验证结果："
for task in "${TASKS[@]}"; do
    if [ -f "tasks/$task/groundtruth/measurement.json" ]; then
        echo "  ✓ $task: measurement.json 已更新"
    else
        echo "  ✗ $task: measurement.json 缺失"
    fi
done
