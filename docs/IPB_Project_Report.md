# Intent-Perf-Bench (IPB) 项目进展报告

**日期**: 2026-08-12  
**作者**: hansirui_3rd

---

## 一、项目背景与动机

当前代码 Agent 的 benchmark 主要关注两类能力：功能正确性（能不能写出正确代码）和指令跟随（能不能执行指定任务）。但现实工程中，Agent 面临的真实挑战往往更复杂——尤其是**性能优化类任务**：

- 问题描述可能是不完整的（"系统变慢了"，没有具体指向）
- 用户提供的线索可能是错误的（指向了错误的瓶颈方向）
- 真正的根因隐藏在多文件、多模块的代码库中

**核心问题**: *当用户提供了误导性信息，Agent 能否通过证据驱动的推理，自行识别出真实的性能瓶颈？*

Intent-Perf-Bench（IPB）旨在量化评估这一能力。

---

## 二、Benchmark 设计

### 2.1 任务结构

每个 IPB 任务包含：
- 一个模拟真实工程的代码仓库（含性能回归）
- 性能测量基准（benchmark 脚本，有明确的通过阈值）
- 4 个变体，控制"给 Agent 的信息量"

**四个变体定义**：

| 变体 | 用户描述内容 |
|------|------------|
| `exact` | 完整的诊断证据（profiler 输出、git 历史、benchmark 结果） |
| `fuzzy` | 模糊描述（"系统变慢了"）+ 部分证据 |
| `misleading` | 明确指向**错误方向**的描述（如"数据加载太慢"） |
| `target_known` | 直接告知目标模块/文件名，不提供误导 |

### 2.2 核心评估指标

**通过率（Pass Rate）**: Agent 是否成功修复了性能问题（benchmark 通过）

**区分度指标（Discrimination Metrics）**:
- **FuzzyGap** = Pass(exact) − Pass(fuzzy)：衡量精确证据的价值
- **MisleadingGap** = Pass(fuzzy) − Pass(misleading)：衡量误导信息的干扰程度

MisleadingGap > 0 表示误导有效——Agent 在有误导时确实表现更差。这是 benchmark 的核心信号。

### 2.3 任务难度公式

基于实验，总结出任务有效性的经验公式：

```
难度 = 搜索空间大小 × 证据间接性 × 误导可信度
```

- **搜索空间大小**：库内部回归（多文件）>> 用户脚本回归（单文件）
- **证据间接性**：profiler 指向模块但不暴露函数名为"中"；benchmark 直接输出函数名为"低"
- **误导可信度**：误导方向在总耗时中的占比（需达到约 10–25%）

---

## 三、已构建任务

### 任务概览

| 任务 ID | 反模式 | Speedup | 误导方向 | 误导占比 | 状态 |
|---------|--------|---------|---------|---------|------|
| ipb_dev_001 | pandas 内部 M8→i8 比较 | ~2x | parquet I/O 慢 | ~6% | 备用（需 Docker） |
| ipb_dev_002 | groupby.apply() vs .agg() | 7.76x | parquet 读取慢 | 0% | 已测（太简单） |
| ipb_dev_003 | iterrows() 行遍历 | 1451x | Export I/O 慢 | ~50% | ✅ 有效 |
| ipb_dev_004 | apply(axis=1) 行遍历 | 297x | Load I/O 慢 | ~19% | ✅ 有效 |
| ipb_dev_005 | list iteration + append | 3.35x | Load I/O 慢 | ~6% | ✅ 有效 |

### 任务代码结构示例（ipb_dev_003）

```
tasks/ipb_dev_003/workspace/
├── pipeline/
│   ├── loader.py       # 数据加载（含 I/O 模拟）
│   ├── transformer.py  # ← 真实瓶颈所在
│   ├── exporter.py     # ← 误导方向（"Export 慢"）
│   └── validator.py
├── benchmarks/
│   └── pipeline_bench.py  # 性能测试，threshold = 0.35s
├── profiler_output.txt    # exact 变体的额外证据
└── git.log
```

**回归方式**（以 ipb_dev_003 为例）：
- Baseline：`transformer.py` 使用 `groupby().cumsum()`（向量化，0.052s）
- Regressed：`transformer.py` 使用 `iterrows()` 逐行迭代（1451x 慢，85.3s）
- commit message 写成"可维护性重构"，不暴露性能问题

---

## 四、实验结果

### 4.1 三个有效任务的测试结果

每个变体各运行 10 次（claude-haiku-4-5），共 ~120 次测试：

**ipb_dev_003**（iterrows，误导占比 ~50%）

| 变体 | 通过率 | 平均轮数 | 首次触达目标轮数 |
|------|--------|---------|---------------|
| exact | 73% | 78 | 2.5 |
| fuzzy | 70% | 52 | 2.1 |
| misleading | 50% | 65 | 3.2 |
| target_known | 70% | 53 | 2.8 |

**MisleadingGap = +20.0%**

---

**ipb_dev_004**（apply(axis=1)，误导占比 ~19%）

| 变体 | 通过率 | 平均轮数 | 首次触达目标轮数 |
|------|--------|---------|---------------|
| exact | 100% | 48 | 6.1 |
| fuzzy | 100% | 51 | 5.3 |
| misleading | 60% | 50 | 4.4 |
| target_known | 90% | 44 | 4.6 |

**MisleadingGap = +40.0%**

---

**ipb_dev_005**（list iteration，误导占比 ~6%）

| 变体 | 通过率 | 平均轮数 | 首次触达目标轮数 |
|------|--------|---------|---------------|
| exact | 70% | 49 | 1.1 |
| fuzzy | 90% | 55 | 2.1 |
| misleading | 70% | 58 | 2.1 |
| target_known | 73% | 65 | 1.5 |

**MisleadingGap = +20.0%**

---

### 4.2 对照组：ipb_dev_002（零区分度任务）

| 变体 | 通过率 |
|------|--------|
| exact | 100% |
| fuzzy | 100% |
| misleading | 100% |

**MisleadingGap = 0%**

原因：benchmark 脚本输出直接暴露了目标函数名，搜索空间（单文件）太小。即使用户说"parquet 慢"，Agent 也能在第 1 轮就找到正确答案。

---

### 4.3 核心发现：误导占比的"甜点区"

| 任务 | 误导占比 | MisleadingGap |
|------|---------|--------------|
| dev_002 | 0% | 0% |
| dev_005 | ~6% | +20% |
| dev_003 | ~50% | +20% |
| dev_004 | ~19% | **+40%** ← 最强 |

**发现**：误导效果并非随占比单调递增，约 15–25% 的占比产生最强的干扰效果。

**可能的解释**：
- 占比太低（6%）：Agent 能通过实测反驳（"只有 6% 的时间，不是瓶颈"）
- 占比太高（50%）：Agent 更倾向于"两边都查一查"，最终仍找到真实瓶颈
- 占比 ~19%（"甜点区"）：足够可信以形成先验，同时不够明显以触发全面排查

这与认知科学中的"锚定效应"相符——适度的误导会产生认知锚点，但过度的误导会触发怀疑机制。

---

## 五、方法论总结

### 有效任务的设计规则（v2 标准）

1. **搜索空间**：使用 3–8 个模块的库内部代码，不能是单文件用户脚本
2. **证据间接性**：profiler/benchmark 只指向模块，不暴露目标函数名
3. **误导占比**：误导方向占总耗时的 15–25%（甜点区）
4. **环境无依赖**：避免特定版本 Docker 依赖，确保可重现
5. **Speedup 足够大**：至少 3x 以上，确保基准测试能稳定区分通过/失败

### Benchmark 基础设施

- **评测 runner**：`scripts/run_agent.py`，支持任意任务/变体/模型组合，后台并行运行
- **Workspace 重置**：每次测试前自动 `git reset --hard` 到回归版本，确保一致起点
- **轨迹分析**：记录 `turns_to_real_target`、`modified_causal_file`、`profiled` 等过程指标

---

## 六、当前状态

**已完成**：
- ✅ 完整评测基础设施（runner、结果分析、workspace 管理）
- ✅ 3 个有效任务（dev_003、dev_004、dev_005），共 ~120 次测试
- ✅ 误导占比梯度实验（6%、19%、50% 三个数据点）
- ✅ 任务难度公式实证验证

**待完成**：
- 扩展到 5 个有效任务（目前 3 个）
- 在更多模型上测试（目前仅 claude-haiku-4-5）
- Multi-round 实验（pass@k + oracle-feedback @k）
- 技术报告/论文

---

## 七、下一步计划

1. **构建 ipb_dev_006**：设计新的误导维度（不再是"I/O 慢"，尝试"数据量大"或"并发竞争"类型）
2. **多模型对比**：在 claude-sonnet-5 上重跑已有任务，观察模型能力差异
3. **写技术报告**：整理方法论、实验数据、核心发现


**设计意图（脚本层面）**：从 SWE-fficiency HuggingFace 数据集里筛选真实的性能优化 PR，走一条自动化流水线：
```
01_select_candidates.py  → 按 speedup、repo筛选候选
02_build_task.py         → 转换为 IPB 目录结构
03_generate_variants.py  → 用 LLM 生成四个prompt变体
04_measure_baseline.py   → 测量基线性能
```

**有效的五个任务（003/004/005/006/027）全部是从头手写的**，没有借用任何外部代码库的代码，场景设计参考了 SWE-fficiency 里常见的 pandas 反模式（iterrows、apply、concat-in-loop）。

**实际执行**：

| 任务                    | 来源                                                                                                                                     |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| ipb_dev_001             | ✅ 真实 SWE-fficiency 任务：`pandas-dev__pandas-38248`（DatetimeLike `_cmp_method` 的 M8→i8 比较优化），provenance = "legacy"            |
| ipb_dev_002             | 手工构建，但 `inspiration` 来自 SWE-fficiency 里的 `groupby.apply vs .agg` 模式（从 pandas-45247/56061 提取 pattern，自己写代码）        |
| **003/004/005/006/027** | **完全手工构建**，没有 intent.json（groundtruth 目录是空的），是看了001/002的实验结果之后，针对"有效任务设计原则"从头写的 synthetic 任务 |

001 的真实任务（pandas 内部代码，需要 Docker环境）跑起来太麻烦，区分度也不理想。所以从002开始转向了"手工构建 synthetic pipeline"的路线——自己设计场景、写pipeline 代码、引入回归、伪造 git.log 和 profiler_output.txt。

