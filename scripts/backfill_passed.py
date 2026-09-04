#!/usr/bin/env python3
"""对已有结果文件补充 passed 判定"""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
RESULTS_DIR = ROOT / "results"
TASKS_DIR = ROOT / "tasks"

def check_passed(task_id: str, workspace_dir: Path) -> tuple[bool, str]:
    """运行基准测试判定是否通过"""
    if task_id == "ipb_dev_001":
        bench_script = workspace_dir / "benchmarks" / "datetime_compare.py"
    elif task_id == "ipb_dev_002":
        bench_script = workspace_dir / "benchmarks" / "report_bench.py"
    elif task_id == "ipb_dev_003":
        bench_script = workspace_dir / "benchmarks" / "pipeline_bench.py"
    else:
        return False, "Unknown task"

    if not bench_script.exists():
        return False, f"Benchmark script not found: {bench_script}"

    try:
        result = subprocess.run(
            ["python3", str(bench_script)],
            cwd=str(workspace_dir),
            capture_output=True,
            text=True,
            timeout=300
        )
        output = result.stdout + result.stderr
        passed = "PASS" in output and result.returncode == 0
        return passed, output
    except subprocess.TimeoutExpired:
        return False, "Benchmark timeout"
    except Exception as e:
        return False, f"Benchmark error: {e}"

def main():
    count_updated = 0
    count_skipped = 0

    for result_path in sorted(RESULTS_DIR.glob("ipb_dev_*.json")):
        data = json.loads(result_path.read_text())

        # 跳过已有 passed 字段的
        if "passed" in data:
            count_skipped += 1
            continue

        task_id = data.get("task_id", "")
        if not task_id:
            print(f"跳过 {result_path.name}: 缺少 task_id")
            continue

        # 应用 diff 到 workspace，然后运行基准测试
        workspace_dir = TASKS_DIR / task_id / "workspace"
        if not workspace_dir.exists():
            print(f"跳过 {result_path.name}: workspace 不存在")
            continue

        # 重置 workspace
        subprocess.run(
            ["git", "reset", "--hard", "HEAD"],
            cwd=str(workspace_dir),
            capture_output=True
        )
        subprocess.run(
            ["git", "clean", "-fd"],
            cwd=str(workspace_dir),
            capture_output=True
        )

        # 应用 diff（如果有）
        final_diff = data.get("final_diff", "")
        if final_diff:
            # 从 diff 提取修改的文件并写入
            # 简单方法：如果 modified_causal_file=True，说明修改了正确文件
            # 直接从 trajectory 提取最后的 write_file 调用
            trajectory = data.get("trajectory", [])
            for t in reversed(trajectory):
                if t.get("type") == "tool_call" and t.get("tool") == "write_file":
                    tool_input = t.get("input", {})
                    path = tool_input.get("path", "")
                    content = tool_input.get("content", "")
                    if path and content:
                        target = workspace_dir / path
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_text(content)
                        break

        # 运行基准测试
        passed, benchmark_output = check_passed(task_id, workspace_dir)

        # 更新结果文件
        data["passed"] = passed
        data["benchmark_output"] = benchmark_output
        result_path.write_text(json.dumps(data, indent=2, default=str) + "\n")

        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} {result_path.name}")
        count_updated += 1

    print(f"\n更新: {count_updated}, 跳过: {count_skipped}")

if __name__ == "__main__":
    main()
