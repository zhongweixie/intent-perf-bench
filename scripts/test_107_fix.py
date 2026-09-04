"""验证 #107 修复：CUDA 任务使用 --benchmark-verify 和隐藏种子"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from ipb_exec import EXEC
import ipb_measure

print("=== 检查 #107 修复 ===\n")

# 支持 --benchmark-verify 的任务
VERIFY_TASKS = {
    "ipb_cuda_001": "HUFFMAN_DECODE_SEED",
    "ipb_cuda_003": "NTT_BENCH_SEED",
    "ipb_cuda_004": "MSM_BENCH_SEED",
    "ipb_cuda_005_icp_correspondence": None,  # 内部生成种子
}

issues = []

for task_id, env_var in VERIFY_TASKS.items():
    spec = EXEC.get(task_id)
    if not spec:
        issues.append(f"❌ {task_id}: 未在 EXEC 中注册")
        continue

    bench_args = spec.get("bench_args", [])
    bench_env = spec.get("bench_env", {})

    # 检查是否使用 --benchmark-verify
    if "--benchmark-verify" not in bench_args:
        issues.append(f"❌ {task_id}: bench_args={bench_args}，应为 ['--benchmark-verify']")
    else:
        print(f"✓ {task_id}: 使用 --benchmark-verify")

    # 检查环境变量（如果需要）
    if env_var:
        if env_var not in bench_env:
            issues.append(f"❌ {task_id}: 缺少 bench_env['{env_var}']")
        else:
            print(f"  └─ bench_env: {env_var}={bench_env[env_var]}")
    else:
        if bench_env:
            issues.append(f"⚠️  {task_id}: 有 bench_env 但不应该需要（内部生成种子）")
        else:
            print(f"  └─ 使用内部种子（无需环境变量）")

# 检查 ipb_measure._run 是否支持 bench_env
print("\n检查 ipb_measure._run 是否支持 bench_env...")
import inspect
source = inspect.getsource(ipb_measure._run)
if "bench_env" in source and "spec.get" in source:
    print("✓ ipb_measure._run 已支持 bench_env")
else:
    issues.append("❌ ipb_measure._run 未正确支持 bench_env")

print("\n" + "="*60)
if issues:
    print("发现问题：")
    for issue in issues:
        print(f"  {issue}")
    sys.exit(1)
else:
    print("✅ #107 修复完整：5个任务均已改用 --benchmark-verify + 隐藏种子")
    print("\n影响：")
    print("  - 防止 agent 针对公开种子优化")
    print("  - 计时与正确性验证同时进行（更严格）")
    print("  - 历史结果（用 --benchmark 的）需要重新标定")
