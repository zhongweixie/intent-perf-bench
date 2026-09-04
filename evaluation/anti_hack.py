"""
Anti-hack 检查：防止 agent 通过修改 workload/测试/评测脚本来伪造成功。

检查范围：
1. workload 脚本（scripts/reproduce.py）未被修改
2. 测试文件未被修改
3. evaluation/ 目录下的脚本未被修改
4. 性能阈值来源文件未被修改（如 .github/workflows/performance.yml）
"""

import hashlib
import json
import subprocess
from pathlib import Path


# 受保护路径（相对于 workspace/）——agent 不得修改
PROTECTED_PATHS = [
    "scripts/reproduce.py",
    "data/",
    ".github/workflows/",
]


def compute_file_hash(path: Path) -> str:
    """计算文件 SHA-256。"""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_baseline_hashes(task_dir: Path) -> dict:
    """加载基线文件哈希（在 workspace 建立后、agent 运行前记录）。"""
    hash_file = task_dir / "evaluation" / "baseline_hashes.json"
    assert hash_file.exists(), (
        f"基线哈希文件不存在: {hash_file}\n"
        "请在 agent 运行前执行: python evaluation/anti_hack.py --task-id <id> --record"
    )
    return json.loads(hash_file.read_text())


def record_baseline_hashes(task_dir: Path, test_files: list[str]):
    """记录 workspace 中受保护文件的基线哈希。在 agent 运行前调用。"""
    workspace = task_dir / "workspace"
    hashes = {}

    # workload 脚本
    reproduce = workspace / "scripts" / "reproduce.py"
    if reproduce.exists():
        hashes[str(reproduce.relative_to(workspace))] = compute_file_hash(reproduce)

    # 测试文件
    for tf in test_files:
        p = workspace / "repo" / tf
        if p.exists():
            hashes[str(p.relative_to(workspace))] = compute_file_hash(p)

    # 整个 evaluation/ 目录
    eval_dir = task_dir / "evaluation"
    for f in eval_dir.rglob("*.py"):
        hashes[f"evaluation/{f.name}"] = compute_file_hash(f)

    out = task_dir / "evaluation" / "baseline_hashes.json"
    out.write_text(json.dumps(hashes, indent=2) + "\n")
    print(f"已记录 {len(hashes)} 个受保护文件的基线哈希 → {out}")
    return hashes


def check_integrity(task_dir: Path) -> dict:
    """
    将当前文件与基线哈希比较，返回违规列表。

    Returns:
        {
            "clean":     bool,
            "violations": list[{"path": str, "reason": str}]
        }
    """
    workspace = task_dir / "workspace"
    baseline = load_baseline_hashes(task_dir)
    violations = []

    for rel_path, expected_hash in baseline.items():
        if rel_path.startswith("evaluation/"):
            actual_path = task_dir / rel_path
        else:
            actual_path = workspace / rel_path

        if not actual_path.exists():
            violations.append({"path": rel_path, "reason": "文件被删除"})
            continue

        actual_hash = compute_file_hash(actual_path)
        if actual_hash != expected_hash:
            violations.append({"path": rel_path, "reason": "文件被修改"})

    return {"clean": len(violations) == 0, "violations": violations}


def check_git_modified_files(repo_dir: Path, protected_prefixes: list[str]) -> list[str]:
    """
    检查 git repo 中被修改的文件是否触碰了受保护路径。
    返回违规文件列表。
    """
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=str(repo_dir), capture_output=True, text=True
    )
    modified = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    violations = []
    for f in modified:
        for prefix in protected_prefixes:
            if f.startswith(prefix):
                violations.append(f)
    return violations
