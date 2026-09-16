# Intent-Perf-Bench 上传状态报告

**更新时间**: 2026-09-16  
**最后验证**: 所有数据已确认可公开访问

---

## ✅ 已完整上传并可公开访问

### 1. Git仓库 (公开)
**地址**: https://github.com/zhongweixie/intent-perf-bench  
**状态**: ✅ PUBLIC

**包含内容** (~550个文件):
- ✅ **61个任务定义** (373个文件)
  - `tasks/*/variants/` - 4种prompt变体
  - `tasks/*/evaluation/` - 评测配置
  - `tasks/*/groundtruth/` - 参考实现
  - `tasks/*/task_metadata.json` - 元数据
  - ❌ `tasks/*/workspace/` - 在Release中

- ✅ **核心代码**
  - `schemas/` - JSON Schema (1个)
  - `scripts/` - 构建和评测脚本 (41个)
  - `evaluation/` - 评测框架 (4个)
  - `requirements.txt`, `SETUP.sh`, `LICENSE`

- ✅ **文档** (35个)
  - `README.md` - 主文档
  - `REBUILD_GUIDE.md` - 重建指南
  - `CONTAINERS.md` - 容器说明
  - `DEPLOYMENT_GUIDE.md` - 部署指南
  - `docs/RECOMMENDED_TASKS.md` - 推荐任务
  - `docs/` - 详细设计文档

- ✅ **实验结果** (40个关键实验)
  - `results/summary/` - 汇总报告 (3个)
  - `results/key_experiments/` - 关键实验 (37个)

---

### 2. GitHub Release v1.0
**地址**: https://github.com/zhongweixie/intent-perf-bench/releases/tag/v1.0  
**状态**: ✅ 所有文件可公开下载

| 文件 | 大小 | 状态 | 下载链接 |
|------|------|------|----------|
| **ipb_workspaces_v1.0.tar.gz** | 710MB | ✅ | [下载](https://github.com/zhongweixie/intent-perf-bench/releases/download/v1.0/ipb_workspaces_v1.0.tar.gz) |
| ipb_seed_data.tar.gz | 239MB | ✅ | [下载](https://github.com/zhongweixie/intent-perf-bench/releases/download/v1.0/ipb_seed_data.tar.gz) |
| ipb_full_experiment_results_v1.0.tar.gz | 3MB | ✅ | [下载](https://github.com/zhongweixie/intent-perf-bench/releases/download/v1.0/ipb_full_experiment_results_v1.0.tar.gz) |

**workspace内容**:
- 61个任务的完整工作区
- 源代码仓库（pandas, numpy等）
- 测试数据和benchmark脚本
- 基准性能测量结果

---

### 3. OneDrive (容器镜像)
**状态**: ✅ 已上传

| 文件 | 大小 | 用途 |
|------|------|------|
| pytorch_cutile.sif | 9.1GB | 12个CUDA任务的Singularity容器 |

**下载链接**: [OneDrive链接](https://hkustconnect-my.sharepoint.com/personal/zxiebk_connect_ust_hk/_layouts/15/download.aspx?share=IQDbaDspfcxLQZGsKHx9hv-GAdtBT9Vvnk737xMQz3ny0Lo)

链接已写入: `CONTAINERS.md`

---

## 📊 数据完整性

### 总计上传数据
| 位置 | 大小 | 内容 |
|------|------|------|
| Git仓库 | ~50MB | 代码+文档+任务定义 |
| GitHub Release | ~952MB | workspace+seed+实验结果 |
| OneDrive | 9.1GB | Singularity容器 |
| **总计** | **~10GB** | 完整benchmark环境 |

### 文件分布验证
```
Git仓库内容:
├── schemas/ (1个文件)
├── scripts/ (41个Python文件)
├── evaluation/ (4个Python文件)
├── tasks/ (373个文件，61任务定义)
├── docs/ (35个文档)
├── results/summary/ (3个汇总)
├── results/key_experiments/ (37个关键实验)
├── LICENSE, README.md, REBUILD_GUIDE.md等
└── requirements.txt, SETUP.sh

Release v1.0内容:
├── ipb_workspaces_v1.0.tar.gz
│   └── tasks/*/workspace/ (61个完整工作区)
├── ipb_seed_data.tar.gz (可选)
└── ipb_full_experiment_results_v1.0.tar.gz (可选)

OneDrive内容:
└── pytorch_cutile.sif (CUDA任务容器)
```

---

## 🎯 用户重建验证

用户可以通过以下5步完整重建环境：

```bash
# 1. 克隆仓库 (50MB, ~10秒)
git clone https://github.com/zhongweixie/intent-perf-bench.git
cd intent-perf-bench

# 2. 下载workspace (710MB, ~2分钟)
wget https://github.com/zhongweixie/intent-perf-bench/releases/download/v1.0/ipb_workspaces_v1.0.tar.gz
tar -xzf ipb_workspaces_v1.0.tar.gz

# 3. 重建可生成数据 (3秒)
python3 tasks/ipb_dev_030/workspace/generate_data.py  # 生成test_events.json (17MB)
python3 tasks/ipb_dev_033/workspace/generate_data.py  # 生成test_records.json (40MB)

# 4. 安装依赖
pip install -r requirements.txt

# 5. 运行评测
python evaluation/evaluate.py --task-id ipb_dev_007 --variant fuzzy
```

**验证**: ✅ 所有步骤均有完整文档（REBUILD_GUIDE.md）

---

## ✅ 推荐任务

详见 `docs/RECOMMENDED_TASKS.md`

**第一梯队**（强区分度，优先推荐）:
1. `ipb_dev_007` - 数据结构选择，misleading慢67×，区分度−98.5%
2. `ipb_dev_038` - 算法复杂度，慢6.9×，区分度−85.5%
3. `ipb_dev_037` - 缓存策略，慢6.3×，区分度−84.1%
4. `ipb_cpu_001_gaussian_blur` - SIMD向量化，慢1.9×，区分度−47.9%
5. `ipb_dev_012` - 字符串操作，慢1.4×，区分度−27.1%

---

## 📝 关键修复记录

### 问题1: workspace目录缺失 ✅ 已修复
- **发现**: workspace目录被`.gitignore`排除，未推送到Git
- **原因**: 设计上workspace应通过Release分发（710MB太大）
- **状态**: ✅ 已打包并上传到Release v1.0

### 问题2: Release文件404 ✅ 已修复
- **发现**: Release文件存在但返回404错误
- **原因**: 仓库设置为private，Release文件无法公开访问
- **修复**: 将仓库改为public
- **验证**: ✅ 所有Release文件现可公开下载

### 问题3: 文档引用的下载链接失效 ✅ 已修复
- **修复前**: README等文档中的下载链接都是404
- **修复后**: 所有下载链接已验证可用
- **状态**: ✅ 用户可直接按文档操作

---

## 📋 Git提交历史

1. **b5f2ee3** (2026-09-04) - 初始部署配置
2. **8a07824** (2026-09-05) - 添加容器OneDrive链接
3. **c793dd8** (2026-09-05) - 添加推荐任务和重建指南
4. **921544c** (2026-09-05) - 添加MIT License
5. **[今日]** (2026-09-16) - 修复workspace缺失和Release访问问题

---

## ❌ 未上传的内容（有意排除）

### 临时数据（已清理）
- ❌ `.scratch/` (687MB) - 批量测试临时工作区
- ❌ `ipb_py310_env/` (282MB) - Python虚拟环境
- ❌ `slurm_outputs/` (184KB) - SLURM日志
- ❌ `seed/*.jsonl` - 中间处理文件

### 可重建数据（已清理）
- ❌ `tasks/ipb_dev_030/workspace/test_events.json` (49MB)
  - 10秒可重建，有生成脚本
- ❌ `tasks/ipb_dev_033/workspace/test_records.json` (40MB)
  - 15秒可重建，有生成脚本

### 历史数据（已归档）
- ❌ `results/*_run*.json` (1115个文件)
  - 已排除，关键实验在`results/key_experiments/`
  - 完整历史在Release的`ipb_full_experiment_results_v1.0.tar.gz`

---

## ✅ 最终结论

### 所有重要内容已上传且可公开访问！

✅ **代码和文档** → Git仓库（public）  
✅ **Workspace数据** → GitHub Release v1.0  
✅ **容器镜像** → OneDrive（链接在文档中）  
✅ **实验结果** → Git仓库 + Release（完整历史）

### 用户可以：
1. ✅ 克隆公开仓库
2. ✅ 下载所有Release文件
3. ✅ 按REBUILD_GUIDE.md完整重建环境
4. ✅ 运行61个任务的评测
5. ✅ 查看推荐任务和实验结果

**项目状态**: ✅ **Production Ready and Publicly Available**

---

**维护**: @zhongweixie  
**仓库**: https://github.com/zhongweixie/intent-perf-bench  
**Release**: https://github.com/zhongweixie/intent-perf-bench/releases/tag/v1.0  
**文档**: [REBUILD_GUIDE.md](REBUILD_GUIDE.md) | [RECOMMENDED_TASKS.md](docs/RECOMMENDED_TASKS.md)
