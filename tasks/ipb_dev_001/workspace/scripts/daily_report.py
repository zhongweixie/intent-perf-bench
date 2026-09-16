"""
daily_report.py — 每日交易时效性报告生成脚本

使用方式：
    python scripts/daily_report.py [--data-dir data/] [--output-dir /tmp/reports/]

描述：
    加载昨日交易记录（parquet），与账户参考表合并，
    判断每笔交易是否在截止时间前完成，输出时效违规统计。

典型运行时间（正常状态）：约 2-4 秒
如果你的机器上明显更慢，请联系 @ops-platform。
"""

import argparse
import pathlib
import sys
import time

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# 数据生成（如果样本文件不存在）
# ---------------------------------------------------------------------------

def ensure_sample_data(data_dir: pathlib.Path, n_rows: int = 10_000_000):
    data_dir.mkdir(parents=True, exist_ok=True)
    tx_path   = data_dir / "transactions.parquet"
    ref_path  = data_dir / "accounts_ref.parquet"

    if not tx_path.exists():
        print(f"  生成样本交易数据（{n_rows:,} 行）...", file=sys.stderr)
        rng = np.random.default_rng(42)
        base = pd.date_range("2024-01-01", periods=n_rows, freq="ms")
        df_tx = pd.DataFrame({
            "tx_id":        np.arange(n_rows, dtype=np.int64),
            "account_id":   rng.integers(1, 50_001, size=n_rows),
            "amount":       rng.uniform(1.0, 10_000.0, size=n_rows).round(2),
            "region":       rng.choice(["APAC", "EMEA", "AMER", "LATAM"], size=n_rows),
            "tx_time":      base,                                          # DatetimeIndex → DatetimeArray
            "deadline":     base + pd.to_timedelta(                        # 截止时间（随机偏移）
                                rng.integers(1, 3601, size=n_rows), unit="s"),
            "status":       rng.choice(["active","pending","closed"], size=n_rows,
                                        p=[0.7, 0.2, 0.1]),
        })
        df_tx.to_parquet(tx_path, index=False)

    if not ref_path.exists():
        print("  生成样本账户参考表...", file=sys.stderr)
        account_ids = np.arange(1, 50_001, dtype=np.int64)
        df_ref = pd.DataFrame({
            "account_id":   account_ids,
            "account_tier": np.random.choice(["gold","silver","bronze"], size=len(account_ids)),
            "sla_hours":    np.random.choice([1, 4, 24], size=len(account_ids)),
        })
        df_ref.to_parquet(ref_path, index=False)

    return tx_path, ref_path


# ---------------------------------------------------------------------------
# 报告生成逻辑
# ---------------------------------------------------------------------------

def load_data(tx_path: pathlib.Path, ref_path: pathlib.Path):
    """从 parquet 加载数据（parquet 读取步骤）。"""
    df_tx  = pd.read_parquet(tx_path)
    df_ref = pd.read_parquet(ref_path)
    return df_tx, df_ref


def filter_active(df: pd.DataFrame) -> pd.DataFrame:
    """只保留活跃账户的交易。"""
    return df[df["status"] == "active"].copy()


def merge_accounts(df_tx: pd.DataFrame, df_ref: pd.DataFrame) -> pd.DataFrame:
    """与账户参考表合并，获取 SLA 信息。"""
    return df_tx.merge(df_ref, on="account_id", how="left")


def compute_violations(df: pd.DataFrame) -> pd.Series:
    """
    判断每笔交易是否在截止时间前完成。
    返回布尔 Series：True = 违规（tx_time > deadline）。

    NOTE: 此步骤在 10M 行规模时占据大部分运行时间。
    """
    # DatetimeArray < DatetimeArray 比较
    return df["tx_time"] > df["deadline"]


def group_by_region(df: pd.DataFrame, violations: pd.Series) -> pd.DataFrame:
    """按地区统计违规率。"""
    df = df.copy()
    df["violated"] = violations
    return (
        df.groupby("region")["violated"]
        .agg(["sum", "count", "mean"])
        .rename(columns={"sum": "violations", "count": "total", "mean": "rate"})
        .sort_values("rate", ascending=False)
    )


def render_report(summary: pd.DataFrame, elapsed: float):
    """输出报告摘要。"""
    print("\n=== 每日时效性报告 ===")
    print(summary.to_string())
    print(f"\n报告生成耗时: {elapsed:.3f}s")


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir",   default="workspace/data",    type=pathlib.Path)
    parser.add_argument("--output-dir", default="/tmp/reports",       type=pathlib.Path)
    args = parser.parse_args()

    t0 = time.perf_counter()

    print("准备数据...", file=sys.stderr)
    tx_path, ref_path = ensure_sample_data(args.data_dir)

    print("加载 parquet...", file=sys.stderr)
    df_tx, df_ref = load_data(tx_path, ref_path)

    print("过滤活跃账户...", file=sys.stderr)
    df_active = filter_active(df_tx)

    print("合并参考表...", file=sys.stderr)
    df_merged = merge_accounts(df_active, df_ref)

    print("计算时效违规（timestamp comparison × 10 批次）...", file=sys.stderr)
    # 模拟10个报表周期（每小时一次）：重复运行比较，使其成为主要瓶颈
    # 典型的生产场景：同一账户集合，滚动更新 deadline 窗口
    for cycle in range(10):
        violations = compute_violations(df_merged)

    print("按地区汇总...", file=sys.stderr)
    summary = group_by_region(df_merged, violations)

    elapsed = time.perf_counter() - t0
    render_report(summary, elapsed)


if __name__ == "__main__":
    main()
