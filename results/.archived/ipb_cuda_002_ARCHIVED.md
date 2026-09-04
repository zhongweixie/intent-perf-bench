# ipb_cuda_002 结果归档记录

**归档日期**: 2026-08-25  
**归档原因**: 任务重复且常量错配，结果不可用

## 问题描述

ipb_cuda_002 与 ipb_cuda_005_icp_correspondence 是同一个 ICP correspondence 任务：
- 相同的标题 "ICP Correspondence CUDA Performance Regression"
- 相同的二进制 `icp_corr`
- 相同的 verify/bench 命令

但两者的 timing 常量不一致：

| 任务 | task.toml 声称的规格 | 实际测量的规格 | 结果 |
|---|---|---|---|
| 002 | N=10000, M=40000, baseline 340ms | N=200000, M=500000, ~65.4ms | 常量完全错配 |
| 005_icp | N=200000, M=500000, baseline 65.4ms | N=200000, M=500000, ~65.4ms | 匹配 |

002 的 24 个结果文件实际测量的是 005_icp 的工作负载，但用了 002 的错误常量：
- `T_regressed = 340.0` (应该是 65.4)
- `T_optimal = 8.0` (应该是 0.294)
- `threshold_ms = 150.0` (硬编码，高于 baseline 65.4，做什么都过)

这导致 9 个 run 实测 65.0-65.4ms（baseline 级别，零改进）却被标记 `passed=True`，improvement_score 计算为 0.83。

## 归档内容

- 24 个 `.json` 结果文件
- 时间范围: run1787371605 - gpt_terra_2_mis_9
- 涉及模型: gpt-5.6-luna, gpt-5.6-terra
- 涉及变体: exact, fuzzy, misleading

## 后续处理

- 任务 002 保留在 `tasks/` 目录但标记为 DEPRECATED
- `run_agent.py` 中删除 002 的配置条目
- 所有 CUDA 评测使用 005_icp（正确常量）
- 如需小规模 ICP 测试，应创建新任务并重新标定 baseline/reference
