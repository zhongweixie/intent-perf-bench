# Intent-Perf-Bench (IPB)

**评测 coding agent 能否从仓库级证据中恢复真实性能优化意图。**

核心问题：当用户的性能优化请求不完整、模糊、或包含错误诊断时，agent 是否能通过
脚本、profile、benchmark、CI 和 SLO 等环境证据，自行恢复真实的优化目标和验收合同？

## 关键区别

| benchmark | 给 Agent 的信息 | 测量内容 |
|---|---|---|
| SWE-fficiency / GSO | 明确 workload + 性能规格 | 执行式优化能力 |
| **IPB (Exact)** | 明确目标 + 阈值 | 基础优化能力（对照组） |
| **IPB (Target-known)** | 告诉优化对象，不告诉阈值 | 性能合同恢复 |
| **IPB (Fuzzy)** | 只给用户式性能抱怨 | 目标＋阈值双恢复 |
| **IPB (Misleading)** | 给出明确但错误的瓶颈诊断 | 抗迎合与实证纠错 |

## 目录结构

```
intent-perf-bench/
├── schemas/           # JSON Schema 定义
├── tasks/             # 任务实例（每个是一个子目录）
│   └── ipb_dev_001/
│       ├── variants/      # exact.md  target_known.md  fuzzy.md  misleading.md
│       ├── workspace/     # repo/ scripts/ data/ docs/ benchmarks/ .github/
│       ├── evaluation/    # correctness/ performance/ anti_hack.py evaluate.py
│       └── groundtruth/   # expert_patch.diff intent.json measurement.json
├── seed/              # 从 SWE-fficiency / GSO 筛选出的候选任务元数据
├── scripts/           # 数据处理和构建脚本（按编号顺序执行）
├── evaluation/        # 通用评测工具
├── docs/              # 协议文档
└── results/           # 运行结果
```

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 克隆参考仓库（评测 harness 参考，不含任务数据）
bash SETUP.sh

# 3. 筛选候选任务（从 HuggingFace 加载 SWE-fficiency）
python scripts/01_select_candidates.py --output seed/swefficiency_candidates.jsonl

# 4. 将一个种子任务转换为 IPB 格式
python scripts/02_build_task.py --seed-id pandas__pandas-50741 --task-id ipb_dev_001

# 5. 用 LLM 生成四个 prompt 变体
python scripts/03_generate_variants.py --task-id ipb_dev_001

# 6. 测量 baseline 和 expert patch 性能
python scripts/04_measure_baseline.py --task-id ipb_dev_001

# 7. 运行完整评测
python evaluation/evaluate.py --task-id ipb_dev_001 --variant fuzzy --patch agent.diff
```

## 主指标

- **Exact Success**: 正确性通过 ∧ 性能达到阈值（对照组）
- **Fuzzy Gap** = Success(Exact) - Success(Fuzzy)：模糊指令造成的成功率损失
- **Misleading Gap** = Success(Fuzzy) - Success(Misleading)：错误诊断造成的额外损失
- **Target Recovery**: agent 修改方向是否落在 primary_targets ∪ acceptable_targets
- **Misdiagnosis Resistance**: agent 是否未将主要资源投入错误方向

## Pre-pilot 判据

**继续做**：Exact 明显高于 Fuzzy，Fuzzy 明显高于 Misleading，阈值文件读取与完成率相关

**暂停重做**：Exact 条件几乎无人成功，或所有模型都不经调查直接命中目标
