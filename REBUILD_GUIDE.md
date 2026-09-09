# Intent-Perf-Bench (IPB) - 完整重建指南

本文档提供从零开始重建 IPB benchmark 环境的完整步骤。

---

## 📦 前置要求

### 必需软件
- Python 3.10+
- Git
- wget 或 curl

### 可选（CUDA 任务）
- GPU (CUDA 12.x)
- Singularity 或 Docker

---

## 🚀 快速开始（5步）

### 1️⃣ 克隆仓库

```bash
git clone https://github.com/zhongweixie/intent-perf-bench.git
cd intent-perf-bench
```

**包含内容**:
- ✅ 61 个任务定义（tasks/*/variants/, groundtruth/, evaluation/）
- ✅ 评测框架（evaluation/）
- ✅ 构建工具（scripts/）
- ✅ 配置文件（schemas/, requirements.txt）
- ✅ 文档（docs/, *.md）

---

### 2️⃣ 下载任务工作区数据

从 [GitHub Release v1.0](https://github.com/zhongweixie/intent-perf-bench/releases/tag/v1.0) 下载:

```bash
# 下载 workspace 数据 (711MB)
wget https://github.com/zhongweixie/intent-perf-bench/releases/download/v1.0/ipb_workspaces_v1.0.tar.gz

# 解压
tar -xzf ipb_workspaces_v1.0.tar.gz

# 验证
ls tasks/ipb_dev_001/workspace/
```

**包含内容**:
- 61 个任务的完整 workspace
- 源代码仓库（如 pandas, numpy）
- 测试数据（parquet, json）
- 基准脚本和配置

---

### 3️⃣ 重建可生成数据（3秒）

两个任务的测试数据被排除以节省空间，需要重建：

```bash
# ipb_dev_030: 生成 10 万条事件数据
python3 tasks/ipb_dev_030/workspace/generate_data.py
# 输出: tasks/ipb_dev_030/workspace/test_events.json (17MB, ~1秒)

# ipb_dev_033: 生成 50 万条记录数据
python3 tasks/ipb_dev_033/workspace/generate_data.py
# 输出: tasks/ipb_dev_033/workspace/test_records.json (40MB, ~2秒)
```

---

### 4️⃣ 安装依赖

#### Python/CPU 任务（56/61 任务）

```bash
pip install -r requirements.txt
```

**包含**:
- numpy, pandas, scipy
- 评测框架依赖

#### CUDA 任务（5/61 任务）

**选项A: 下载 Singularity 容器** (推荐，HPC 环境)

```bash
# 下载容器 (9.1GB)
wget "https://hkustconnect-my.sharepoint.com/personal/zxiebk_connect_ust_hk/_layouts/15/download.aspx?share=IQDbaDspfcxLQZGsKHx9hv-GAdtBT9Vvnk737xMQz3ny0Lo" \
  -O containers/pytorch_cutile.sif

# 验证
singularity exec --nv containers/pytorch_cutile.sif python3 -c "import torch; print(torch.cuda.is_available())"
```

**选项B: 使用 Docker**

```bash
cd containers/
docker build -t pytorch-cutile:local -f Dockerfile .
```

详见 [CONTAINERS.md](CONTAINERS.md)

---

### 5️⃣ 运行第一个评测

```bash
# Python 任务示例
python evaluation/evaluate.py --task-id ipb_dev_007 --variant fuzzy

# CUDA 任务示例（需要 GPU）
singularity exec --nv containers/pytorch_cutile.sif \
  python evaluation/evaluate.py --task-id ipb_cuda_001 --variant fuzzy
```

**预期输出**:
```json
{
  "task_id": "ipb_dev_007",
  "variant": "fuzzy",
  "baseline_time_ms": 450.0,
  "elapsed_time_ms": 0.43,
  "improvement_score": 0.98,
  "passed": true
}
```

---

## ✅ 验证清单

完成上述步骤后，验证环境：

```bash
# 1. 检查 workspace 完整性
ls tasks/ipb_dev_001/workspace/repo/  # 应该看到 pandas 源码
ls tasks/ipb_dev_030/workspace/test_events.json  # 应该存在
ls tasks/ipb_dev_033/workspace/test_records.json  # 应该存在

# 2. 检查任务定义
ls tasks/ipb_dev_007/variants/  # 应该有 fuzzy.md, misleading.md 等
cat tasks/ipb_dev_007/task.json  # 应该有 baseline_ms, reference_ms 等

# 3. 运行快速测试
python evaluation/evaluate.py --task-id ipb_dev_030 --variant fuzzy
python evaluation/evaluate.py --task-id ipb_dev_033 --variant fuzzy

# 4. 检查容器（如果有 GPU）
singularity exec --nv containers/pytorch_cutile.sif \
  python3 -c "import torch; import cuda_tile; print('✓ CUDA环境正常')"
```

---

## 📊 数据完整性

### Git 仓库包含（~50MB）

```
intent-perf-bench/
├── tasks/                      # 61 个任务定义
│   ├── ipb_dev_001/
│   │   ├── variants/           # ✅ fuzzy, misleading, exact, target_known
│   │   ├── evaluation/         # ✅ 评测配置和阈值
│   │   ├── groundtruth/        # ✅ 参考实现
│   │   ├── task.json           # ✅ 任务元数据
│   │   └── workspace/          # ❌ 不在 Git（见 Release）
│   └── ... (60 个其他任务)
├── evaluation/                 # ✅ 评测框架
│   ├── evaluate.py
│   ├── correctness.py
│   ├── performance.py
│   └── anti_hack.py
├── scripts/                    # ✅ 构建工具
│   ├── 01_select_candidates.py
│   ├── 02_build_task.py
│   ├── 03_generate_variants.py
│   ├── 04_measure_baseline.py
│   └── run_agent.py
├── schemas/                    # ✅ JSON Schema 定义
├── docs/                       # ✅ 文档
│   ├── RECOMMENDED_TASKS.md
│   ├── task_design_principles.md
│   └── ...
├── results/summary/            # ✅ 关键实验结果
│   └── misleading_rewrite_test_summary.json
├── README.md                   # ✅ 本文档
├── CONTAINERS.md               # ✅ 容器说明
├── DEPLOYMENT_GUIDE.md         # ✅ 部署指南
└── requirements.txt            # ✅ Python 依赖
```

### Release v1.0 包含（~1GB）

1. **ipb_workspaces_v1.0.tar.gz** (711MB) - 61 个任务 workspace
2. **ipb_seed_data.tar.gz** (240MB) - SWE-efficiency 数据集（可选）
3. **ipb_full_experiment_results_v1.0.tar.gz** (3.2MB) - 1115 个历史测试结果（可选）

### OneDrive 托管

- **pytorch_cutile.sif** (9.1GB) - Singularity 容器（仅 CUDA 任务需要）

---

## 🎯 推荐任务

不确定从哪个任务开始？查看 [docs/RECOMMENDED_TASKS.md](docs/RECOMMENDED_TASKS.md)

**快速推荐**:
```bash
# 强区分度任务（优先）
ipb_dev_007          # 数据结构选择，misleading 慢 67×
ipb_dev_038          # 算法复杂度，慢 6.9×
ipb_dev_037          # 缓存策略，慢 6.3×
ipb_cpu_001_gaussian_blur  # SIMD 向量化，慢 1.9×
ipb_dev_012          # 字符串操作，慢 1.4×
```

---

## 🔧 高级：从头构建新任务

如果你想从 SWE-efficiency 等数据源构建新任务：

```bash
# 1. 下载 seed 数据（可选）
wget https://github.com/zhongweixie/intent-perf-bench/releases/download/v1.0/ipb_seed_data.tar.gz
tar -xzf ipb_seed_data.tar.gz

# 2. 克隆参考仓库
bash SETUP.sh

# 3. 筛选候选任务
python scripts/01_select_candidates.py --output seed/candidates.jsonl

# 4. 构建任务
python scripts/02_build_task.py --seed-id <task-id> --task-id ipb_new_001

# 5. 生成变体 prompt
python scripts/03_generate_variants.py --task-id ipb_new_001

# 6. 测量 baseline 性能
python scripts/04_measure_baseline.py --task-id ipb_new_001
```

---

## 📖 评测流程

### 单任务评测

```bash
python evaluation/evaluate.py \
  --task-id ipb_dev_007 \
  --variant fuzzy \
  --output results/my_test.json
```

### 批量评测

```bash
# 使用 run_agent.py（包含完整 agent 交互）
python scripts/run_agent.py \
  --task ipb_dev_007 \
  --variant fuzzy \
  --model opus-5 \
  --output results/batch/
```

### 对比 fuzzy vs misleading

```bash
# Fuzzy 变体
python scripts/run_agent.py --task ipb_dev_007 --variant fuzzy --model opus-5

# Misleading 变体
python scripts/run_agent.py --task ipb_dev_007 --variant misleading --model opus-5

# 分析区分度
python scripts/analyze_discrimination.py results/batch/ipb_dev_007_*.json
```

---

## 🐛 常见问题

### Q1: workspace 数据缺失

**症状**: `FileNotFoundError: tasks/ipb_dev_001/workspace/repo/`

**解决**: 下载并解压 workspace 数据（步骤 2）

### Q2: test_events.json 或 test_records.json 缺失

**症状**: `FileNotFoundError: test_events.json`

**解决**: 运行生成脚本（步骤 3）

### Q3: CUDA 任务失败

**症状**: `[UNKNOWN CUDA TASK]` 或 `ImportError: cuda_tile`

**解决**:
1. 确认 GPU 可用: `nvidia-smi`
2. 下载容器: 参见步骤 4
3. 使用容器运行: `singularity exec --nv ...`

### Q4: 性能结果与文档不符

**可能原因**:
- CPU/GPU 不同
- Python 版本不同
- 系统负载影响

**建议**: 对比 **相对性能**（baseline vs reference）而非绝对时间

---

## 📚 文档索引

- [RECOMMENDED_TASKS.md](docs/RECOMMENDED_TASKS.md) - 推荐任务清单
- [CONTAINERS.md](CONTAINERS.md) - 容器环境说明
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - 部署和发布指南
- [task_design_principles.md](docs/task_design_principles.md) - 任务设计原则
- [misleading_prompt_rewrite_report.md](docs/misleading_prompt_rewrite_report.md) - Misleading prompt 改进报告

---

## 🤝 贡献

发现问题或有改进建议？欢迎：
1. 提交 Issue: https://github.com/zhongweixie/intent-perf-bench/issues
2. 提交 Pull Request

---

## 📄 许可证

MIT License

---

**项目状态**: ✅ Production Ready  
**最后更新**: 2026-09-05  
**维护者**: @zhongweixie
