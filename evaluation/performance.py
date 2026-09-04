"""
性能测量核心工具：基于 pyperf，控制 CV（变异系数）在指定阈值内。

用于测量 Python workload 脚本的稳定运行时间。
"""

import json
import os
import statistics
import subprocess
import sys
import tempfile
from typing import Optional


def measure_script(
    script: str,
    cwd: str,
    n_runs: int = 9,
    warmup: int = 3,
    max_cv: float = 0.05,
    max_retries: int = 3,
    env: Optional[dict] = None,
) -> dict:
    """
    测量脚本运行时间，返回统计结果。
    如果 CV 超过 max_cv，自动重试（最多 max_retries 次）。

    Returns:
        {
            "median_s": float,
            "mean_s":   float,
            "stdev_s":  float,
            "cv":       float,       # 变异系数（stdev / mean）
            "min_s":    float,
            "max_s":    float,
            "samples":  list[float], # 所有正式测量值（不含 warmup）
            "n_runs":   int,
            "warmup":   int,
        }
    """
    run_env = dict(os.environ)
    if env:
        run_env.update(env)

    for attempt in range(1, max_retries + 1):
        all_times = _run_timed(script, cwd, n_runs + warmup, run_env)
        samples = all_times[warmup:]  # 丢弃 warmup

        median = statistics.median(samples)
        mean   = statistics.mean(samples)
        stdev  = statistics.stdev(samples) if len(samples) > 1 else 0.0
        cv     = stdev / mean if mean > 0 else 0.0

        if cv <= max_cv or attempt == max_retries:
            if cv > max_cv:
                print(
                    f"  警告: CV={cv:.3f} > {max_cv}（尝试 {attempt}/{max_retries}），"
                    f"测量噪声较大，结果仅供参考",
                    file=sys.stderr,
                )
            return {
                "median_s": median,
                "mean_s":   mean,
                "stdev_s":  stdev,
                "cv":       cv,
                "min_s":    min(samples),
                "max_s":    max(samples),
                "samples":  samples,
                "n_runs":   n_runs,
                "warmup":   warmup,
            }
        print(f"  CV={cv:.3f} 超限，重试 {attempt + 1}/{max_retries}...", file=sys.stderr)

    assert False, "unreachable"


def _run_timed(script: str, cwd: str, total_runs: int, env: dict) -> list:
    """逐次运行脚本并记录每次 wall-clock 时间（秒）。"""
    import time
    times = []
    for _ in range(total_runs):
        t0 = time.perf_counter()
        result = subprocess.run(
            [sys.executable, script],
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
        )
        elapsed = time.perf_counter() - t0
        if result.returncode != 0:
            raise RuntimeError(
                f"workload 脚本退出码非零: {result.returncode}\n"
                f"stderr: {result.stderr[-500:]}"
            )
        times.append(elapsed)
    return times


def compute_speedup(baseline_s: float, patched_s: float) -> float:
    """计算加速比（baseline / patched）。"""
    assert patched_s > 0, "patched 运行时间必须大于 0"
    return baseline_s / patched_s


def meets_threshold(baseline_s: float, patched_s: float, threshold: float) -> bool:
    """判断 patch 是否达到要求的加速倍数。"""
    return compute_speedup(baseline_s, patched_s) >= threshold
