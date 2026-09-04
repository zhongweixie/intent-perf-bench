#!/usr/bin/env python3
"""
Validate IPB task completeness and structure
"""

import os
import subprocess
from pathlib import Path

TASK_IDS = [
    "ipb_cuda_001",
    "ipb_cuda_002",
    "ipb_cuda_003",
    "ipb_cuda_004",
    "ipb_cuda_005_l2norm_reduction",
]

REQUIRED_FILES = [
    "task.toml",
    "workspace",
    "workspace/.git",
    "workspace/Makefile",
    "workspace/main.cu",
    "workspace/solve.cu",
    "workspace/solve_baseline.cu",
    "workspace/solve_regression.cu",
]

OPTIONAL_FILES = [
    "benchmarks/bench.sh",
    "variants/fuzzy.md",
    "variants/misleading.md",
]

def check_task(task_id):
    """Check completeness of a single task"""
    base_path = Path(f"/aifs4su/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/tasks/{task_id}")

    if not base_path.exists():
        return {"exists": False}

    result = {
        "exists": True,
        "required": {},
        "optional": {},
        "git_commits": 0,
        "workspace_files": []
    }

    # Check required files
    for file_path in REQUIRED_FILES:
        full_path = base_path / file_path
        result["required"][file_path] = full_path.exists()

    # Check optional files
    for file_path in OPTIONAL_FILES:
        full_path = base_path / file_path
        result["optional"][file_path] = full_path.exists()

    # Check git history
    workspace_path = base_path / "workspace"
    if workspace_path.exists() and (workspace_path / ".git").exists():
        try:
            os.chdir(workspace_path)
            commit_count = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"],
                capture_output=True,
                text=True,
                check=True
            )
            result["git_commits"] = int(commit_count.stdout.strip())

            # List workspace files
            result["workspace_files"] = [f.name for f in workspace_path.iterdir()
                                         if f.is_file() and not f.name.startswith('.')]
        except Exception as e:
            result["git_error"] = str(e)

    return result

def print_task_status(task_id, status):
    """Pretty print task status"""
    print(f"\n{'='*60}")
    print(f"Task: {task_id}")
    print('='*60)

    if not status["exists"]:
        print("❌ Task directory does not exist")
        return

    print("\n📋 Required Files:")
    for file_path, exists in status["required"].items():
        symbol = "✓" if exists else "✗"
        print(f"  {symbol} {file_path}")

    print("\n📝 Optional Files:")
    for file_path, exists in status["optional"].items():
        symbol = "✓" if exists else "✗"
        print(f"  {symbol} {file_path}")

    print(f"\n🔄 Git Commits: {status['git_commits']}")

    if status["workspace_files"]:
        print(f"\n📁 Workspace Files ({len(status['workspace_files'])}):")
        for f in sorted(status["workspace_files"])[:10]:
            print(f"  - {f}")
        if len(status["workspace_files"]) > 10:
            print(f"  ... and {len(status['workspace_files']) - 10} more")

    # Overall completeness
    required_count = sum(status["required"].values())
    total_required = len(status["required"])
    optional_count = sum(status["optional"].values())
    total_optional = len(status["optional"])

    completeness = (required_count / total_required) * 100
    print(f"\n📊 Completeness: {completeness:.1f}% ({required_count}/{total_required} required)")
    print(f"   Optional: {optional_count}/{total_optional}")

def main():
    print("IPB Task Validation Report")
    print("=" * 60)

    summary = {}
    for task_id in TASK_IDS:
        status = check_task(task_id)
        summary[task_id] = status
        print_task_status(task_id, status)

    # Overall summary
    print(f"\n\n{'='*60}")
    print("SUMMARY")
    print('='*60)

    for task_id, status in summary.items():
        if not status["exists"]:
            print(f"❌ {task_id}: Does not exist")
        else:
            req_count = sum(status["required"].values())
            total_req = len(status["required"])
            completeness = (req_count / total_req) * 100

            if completeness == 100:
                symbol = "✅"
            elif completeness >= 80:
                symbol = "⚠️"
            else:
                symbol = "❌"

            print(f"{symbol} {task_id}: {completeness:.0f}% complete, {status['git_commits']} commits")

if __name__ == "__main__":
    main()
