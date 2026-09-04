"""
正确性测试：在仓库环境中运行指定的 pytest 测试文件，返回通过/失败。
"""

import json
import subprocess
import sys
from pathlib import Path


def run_correctness_tests(
    repo_dir: str | Path,
    test_files: list[str],
    timeout: int = 300,
) -> dict:
    """
    运行指定测试文件，返回结构化结果。

    Returns:
        {
            "passed":     bool,
            "returncode": int,
            "stdout":     str,
            "stderr":     str,
            "summary":    str,   # pytest 最后一行（如 "2 passed, 1 failed"）
        }
    """
    if not test_files:
        return {
            "passed": True,
            "returncode": 0,
            "stdout": "",
            "stderr": "",
            "summary": "no tests specified",
        }

    cmd = [
        sys.executable, "-m", "pytest",
        "--tb=short",          # 简洁 traceback
        "--no-header",
        "-q",                  # 安静模式，只显示结果摘要
    ] + list(test_files)

    result = subprocess.run(
        cmd,
        cwd=str(repo_dir),
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    # 从 stdout 末尾提取 pytest 摘要行
    summary_lines = [
        line for line in result.stdout.splitlines()
        if "passed" in line or "failed" in line or "error" in line
    ]
    summary = summary_lines[-1] if summary_lines else "(no summary)"

    return {
        "passed":     result.returncode == 0,
        "returncode": result.returncode,
        "stdout":     result.stdout[-3000:],   # 截断，避免日志爆炸
        "stderr":     result.stderr[-1000:],
        "summary":    summary,
    }
