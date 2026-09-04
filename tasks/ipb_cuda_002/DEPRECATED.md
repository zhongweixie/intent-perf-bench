# ipb_cuda_002 已废弃

## 原因

此任务与 `ipb_cuda_005_icp_correspondence` 重复：

- 相同标题："ICP Correspondence CUDA Performance Regression"
- 相同二进制：`icp_corr`
- 相同验证/benchmark 命令

## 配置错误

`task.toml` 声明：
- N=10000, M=40000
- baseline 340.0 ms
- threshold 25.0 ms

但实际存档结果测量的是：
- N=200000, M=500000（005_icp 的规格）
- baseline ~65.4 ms（005_icp 的 baseline）
- harness 硬编码 threshold 150.0 ms（高于 baseline，做什么都通过）

## 结果作废

24 个结果文件（2026-08-25 移至 `results/archived/ipb_cuda_002_INVALID/`）：
- 9 次 65.0–65.4 ms → 未优化但被判 pass，improvement_score = 0.83（公式用了错误的 340.0 ms baseline）
- 3 次 0.31–4.28 ms → 真实优化，但常量错配导致分数计算错误
- 其余编译失败或并发污染

## 后续行动

保留 `ipb_cuda_005_icp_correspondence` 作为唯一的 ICP 任务。002 任务目录保留作为历史记录，但已从 `run_agent.py` 的所有配置表中移除（`REGRESSED_COMMITS`、`task_info`、`_TASK_CONSTANTS`、`_TIMING_CONSTANTS`）。

---
废弃日期：2026-08-27  
替代任务：ipb_cuda_005_icp_correspondence
