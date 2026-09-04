# 环境配置指南

## 📦 Python 环境

### 版本要求
- **Python**: 3.10+ (测试环境使用 Python 3.10)
- **CUDA**: 11.8+ (用于CUDA任务)

### 创建虚拟环境

```bash
# 方法1: venv
python3.10 -m venv ipb_py310_env
source ipb_py310_env/bin/activate

# 方法2: conda
conda create -n ipb python=3.10
conda activate ipb
```

### 安装依赖

```bash
cd intent-perf-bench
pip install -r requirements.txt
```

---

## 🔧 系统依赖

### CUDA 任务 (ipb_cuda_*)
```bash
# 需要 NVIDIA GPU + CUDA Toolkit
nvcc --version  # 验证 CUDA 安装

# 需要的库
# - CUDA Runtime
# - cuDNN (用于某些任务)
# - CuTe (用于 flash_attention_cutile)
```

### CPU 任务 (ipb_cpu_*)
```bash
# 需要 C/C++ 编译器
gcc --version  # 应该 >= 9.0
g++ --version

# 某些任务需要
# - OpenMP
# - AVX2/AVX-512 支持
```

### Python 任务 (ipb_dev_*)
```bash
# 基本Python依赖已在 requirements.txt 中
# 某些任务可能需要额外包：
pip install torch transformers scikit-learn
```

---

## 🐳 Docker (可选)

某些测试使用 Docker 隔离环境：

```bash
# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 验证
docker --version
```

---

## 📂 目录结构

运行测试后会生成：

```
intent-perf-bench/
├── ipb_py310_env/          # Python虚拟环境 (gitignore)
├── results/                # 测试结果 JSON
│   ├── key_experiments/    # 关键实验数据 (已在git)
│   └── summary/           # 汇总报告 (已在git)
├── seed/                   # 大型数据文件 (gitignore, 见Release)
├── slurm_outputs/         # Slurm日志 (gitignore)
└── tasks/*/workspace/     # 任务工作区 (gitignore)
```

---

## ⚙️ 配置文件

### API Keys (可选)
某些功能需要 LLM API keys：

```bash
# .env 文件 (不要提交到git)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

### Slurm (HPC环境)
如果使用SLURM集群：

```bash
# 查看现有的slurm脚本
ls slurm_*.sh

# 根据你的集群配置修改
# - partition name
# - GPU类型
# - 时间限制
```

---

## ✅ 验证环境

运行以下命令测试环境：

```bash
# 1. Python环境
python --version
pip list | grep -E "anthropic|swebench|pyperf"

# 2. 编译器
gcc --version
nvcc --version

# 3. 任务完整性
python validate_tasks.py

# 4. 运行简单测试 (可选)
# 选择一个简单的任务测试
cd tasks/ipb_dev_007/workspace
python solve.py
```

---

## 🚀 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/zhongweixie/intent-perf-bench.git
cd intent-perf-bench

# 2. 创建环境
python3.10 -m venv ipb_py310_env
source ipb_py310_env/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. (可选) 下载seed数据
# 从 GitHub Release v1.0 下载 ipb_seed_data.tar.gz
# tar -xzf ipb_seed_data.tar.gz

# 5. 运行评测
# 参考 scripts/ 目录中的脚本
```

---

## 🔗 相关资源

- **GitHub仓库**: https://github.com/zhongweixie/intent-perf-bench
- **Release下载**: https://github.com/zhongweixie/intent-perf-bench/releases/tag/v1.0
- **Seed数据说明**: seed/README.md
