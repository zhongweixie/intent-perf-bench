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

### 1. 克隆仓库

```bash
git clone https://github.com/GenseeAI/intent-perf-bench.git
cd intent-perf-bench
```

### 2. 下载任务工作区数据

从 [GitHub Release v1.0](https://github.com/GenseeAI/intent-perf-bench/releases/tag/v1.0) 下载 `ipb_workspaces_v1.0.tar.gz` (711MB)：

```bash
# 下载并解压
wget https://github.com/GenseeAI/intent-perf-bench/releases/download/v1.0/ipb_workspaces_v1.0.tar.gz
tar -xzf ipb_workspaces_v1.0.tar.gz
```

### 3. 重建可生成数据 (3秒)

```bash
python3 tasks/ipb_dev_030/workspace/generate_data.py
python3 tasks/ipb_dev_033/workspace/generate_data.py
```

### 4. 安装依赖

**纯Python任务**:
```bash
pip install -r requirements.txt
```

**CUDA任务** (需要GPU):
```bash
# 选项A: Docker (推荐)
docker pull zwxie/codebench:pytorch-cutile-v1.0

# 选项B: Singularity (HPC环境)
singularity pull docker://zwxie/codebench:pytorch-cutile-v1.0
```

详见 [CONTAINERS.md](CONTAINERS.md)

### 5. 运行评测

```bash
# Python任务
python evaluation/evaluate.py --task-id ipb_dev_001 --variant fuzzy

# CUDA任务 (使用Docker)
docker run --gpus all -v $(pwd):/workspace zwxie/codebench:pytorch-cutile-v1.0 \
  python evaluation/evaluate.py --task-id ipb_cuda_001 --variant fuzzy
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

## 构建新任务 (可选)

如果你想从SWE-fficiency等数据源构建新的IPB任务：

```bash
# 1. 克隆参考仓库
bash SETUP.sh

# 2. 筛选候选任务
python scripts/01_select_candidates.py --output seed/candidates.jsonl

# 3. 构建任务
python scripts/02_build_task.py --seed-id <task-id> --task-id ipb_new_001

# 4. 生成变体
python scripts/03_generate_variants.py --task-id ipb_new_001

# 5. 测量baseline
python scripts/04_measure_baseline.py --task-id ipb_new_001
```

## 文档

- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - 部署和发布指南
- [CONTAINERS.md](CONTAINERS.md) - 容器环境说明
- [docs/](docs/) - 详细设计文档和实验报告
