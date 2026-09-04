#!/usr/bin/env bash
# Intent-Perf-Bench 参考库克隆脚本
# 这些仓库只作为评测 harness 参考，不包含任务数据本身
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REF_DIR="$REPO_ROOT/seed/reference_repos"
mkdir -p "$REF_DIR"

echo "=== 克隆 SWE-fficiency harness ==="
if [ ! -d "$REF_DIR/swefficiency" ]; then
    git clone https://github.com/swefficiency/swefficiency "$REF_DIR/swefficiency"
else
    echo "  已存在，跳过"
fi

echo "=== 克隆 GSO benchmark ==="
if [ ! -d "$REF_DIR/gso" ]; then
    git clone https://github.com/gso-bench/gso "$REF_DIR/gso"
else
    echo "  已存在，跳过"
fi

echo "=== 克隆 SWE-bench（Docker harness 参考）==="
if [ ! -d "$REF_DIR/SWE-bench" ]; then
    git clone https://github.com/princeton-nlp/SWE-bench "$REF_DIR/SWE-bench"
else
    echo "  已存在，跳过"
fi

echo ""
echo "=== 安装 Python 依赖 ==="
pip install -r "$REPO_ROOT/requirements.txt"

echo ""
echo "=== 验证数据集访问 ==="
python - <<'EOF'
from datasets import load_dataset
print("正在测试 SWE-fficiency 数据集访问（只下载元数据）...")
ds = load_dataset("swefficiency/swefficiency", split="test[:1]")
print(f"  字段: {list(ds.features.keys())}")
print(f"  首条 instance_id: {ds[0].get('instance_id', 'N/A')}")
print("  访问成功")
EOF

echo ""
echo "=== 完成 ==="
echo "下一步：python scripts/01_select_candidates.py --output seed/swefficiency_candidates.jsonl"
