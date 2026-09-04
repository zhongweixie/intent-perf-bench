# Intent-Perf-Bench 部署指南

本文档说明如何将IPB项目部署到可公开访问的环境。

---

## 📦 当前项目组成

### 总大小: 17GB

```
9.1GB  - Singularity容器 (containers/)
5.4GB  - 实验结果数据 (seed/)
1.2GB  - 任务工作区 (tasks/)
687MB  - 临时数据 (.scratch/)
282MB  - Python环境 (ipb_py310_env/)
```

---

## 🎯 部署策略

### 1. **Singularity容器 → Docker Hub** (9.1GB)

容器是从官方镜像构建的，可以推送Docker镜像替代：

**原始容器**:
```bash
# 当前使用
containers/ipb_py310.sif (9.1GB)

# 容器内容
FROM nvcr.io/nvidia/pytorch:26.04-py3
RUN pip install --upgrade cuda-tile==1.5.0
```

**推送到Docker Hub**:
```bash
# 创建等效Dockerfile
cat > Dockerfile << 'EOF'
FROM nvcr.io/nvidia/pytorch:26.04-py3
RUN pip install --upgrade cuda-tile==1.5.0
EOF

# 构建并推送
docker build -t zwxie/codebench:pytorch-cutile-v1.0 .
docker push zwxie/codebench:pytorch-cutile-v1.0

# 用户使用
docker pull zwxie/codebench:pytorch-cutile-v1.0
```

**节省**: 9.1GB → 0GB (从Docker Hub拉取)

---

### 2. **实验结果数据** (5.4GB)

**seed/目录内容**:
- 标定实验的完整对话记录 (*.jsonl)
- Misleading prompt改进实验数据
- 19个任务的fuzzy/misleading变体测试结果

**建议**: 
- ✅ **保留并推送到GitHub** - 这是benchmark的重要实验数据
- ✅ 压缩后约2-3GB
- ✅ 用户可选择性下载（Git LFS）

```bash
# 压缩归档
tar -czf ipb_seed_data_v1.0.tar.gz seed/

# 使用Git LFS管理大文件
git lfs track "*.tar.gz"
git add .gitattributes ipb_seed_data_v1.0.tar.gz
git commit -m "Add experimental data with Git LFS"
```

---

### 3. **任务工作区** (1.2GB)

**已优化**:
- ✅ 已删除325MB可重建数据
- ✅ 添加了REBUILD_DATA.md重建说明
- ✅ 更新了.gitignore

**当前保留**:
- ipb_dev_001: pandas源码 (516MB) + 1000万行数据 (256MB) - **必需**
- 其他任务: 小规模数据文件 (<50MB)

**建议**: 
- ✅ **完整推送** - 工作区是benchmark运行的必需环境
- ✅ 用户clone后只需运行2个重建脚本（3秒）

```bash
# 用户clone后重建数据
cd tasks/ipb_dev_030/workspace && python3 generate_data.py  # 1秒
cd ../../ipb_dev_033/workspace && python3 generate_data.py  # 2秒
```

---

### 4. **临时数据** (687MB + 282MB + 184KB)

**可安全删除**:
```bash
rm -rf .scratch/              # 687MB - Claude对话临时文件
rm -rf ipb_py310_env/         # 282MB - 可用requirements.txt重建
rm -rf slurm_outputs/         # 184KB - 旧的slurm日志
```

**节省**: 969MB

---

## 📋 完整部署清单

### ✅ 推送到GitHub

```
intent-perf-bench/
├── tasks/                    # 1.2GB - 任务工作区（完整）
├── seed/                     # 5.4GB - 实验数据（Git LFS压缩）
├── docs/                     # 文档
├── requirements.txt          # Python依赖
├── README.md                 # 主文档
├── DEPLOYMENT_GUIDE.md       # 本文档
└── .gitignore               # 已更新

总计: ~3-4GB (压缩后)
```

### ✅ 推送到Docker Hub

```
zwxie/codebench:pytorch-cutile-v1.0
- 基于: nvcr.io/nvidia/pytorch:26.04-py3
- 包含: cuda-tile==1.5.0
- 大小: ~8GB (在Docker Hub)
```

---

## 🚀 用户使用流程

### 1. 克隆仓库

```bash
git clone https://github.com/zwxie/intent-perf-bench.git
cd intent-perf-bench
```

### 2. 下载容器

**选项A: Docker**
```bash
docker pull zwxie/codebench:pytorch-cutile-v1.0
```

**选项B: 使用本地环境**
```bash
pip install -r requirements.txt
```

### 3. 重建测试数据 (3秒)

```bash
python3 tasks/ipb_dev_030/workspace/generate_data.py
python3 tasks/ipb_dev_033/workspace/generate_data.py
```

### 4. 运行benchmark

```bash
python3 run_benchmark.py --task ipb_dev_001
```

---

## 📊 空间节省汇总

| 项目 | 原始大小 | 部署后 | 节省 |
|------|---------|--------|------|
| Singularity容器 | 9.1GB | 0GB (Docker Hub) | 9.1GB |
| 临时数据 | 969MB | 0MB | 969MB |
| 可重建数据 | 325MB | 0MB | 325MB |
| 实验数据 | 5.4GB | 2-3GB (压缩) | 2-3GB |
| **总计** | **17GB** | **~5GB** | **~12GB** |

---

## ✅ 下一步操作

1. **删除临时数据**: `rm -rf .scratch ipb_py310_env slurm_outputs`
2. **压缩实验数据**: `tar -czf ipb_seed_data_v1.0.tar.gz seed/`
3. **构建Docker镜像**: 创建Dockerfile并推送
4. **提交到GitHub**: `git add . && git commit && git push`

---

**生成时间**: 2026-09-04  
**版本**: v1.0
