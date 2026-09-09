# 推荐任务清单

本文档基于 Opus 5 + 19 任务 misleading prompt 重写实验结果（2026-09-03）。

---

## 📊 任务分级

### 🏆 第一梯队：强区分度任务（推荐优先使用）

这些任务的 misleading prompt 能显著误导模型，导致优化后性能**明显变差**。

| 任务 | 区分度 | Fuzzy耗时 | Misleading耗时 | 效果 | 优化类型 |
|---|---:|---:|---:|---|---|
| **ipb_dev_007** | **−98.5%** | 0.43s | 28.79s | 慢 67× | 数据结构选择 |
| **ipb_dev_038** | **−85.5%** | 0.034s | 0.236s | 慢 6.9× | 算法复杂度 |
| **ipb_dev_037** | **−84.1%** | 0.198s | 1.25s | 慢 6.3× | 缓存策略 |
| **ipb_cpu_001_gaussian_blur** | **−47.9%** | 5.91s | 11.35s | 慢 1.9× | SIMD向量化 |
| **ipb_dev_012** | **−27.1%** | 0.0105s | 0.0144s | 慢 1.4× | 字符串操作 |

**区分度定义**: `(Fuzzy时间 − Misleading时间) / Misleading时间`，**负值越大越好**（misleading 成功误导，优化后更慢）

**使用建议**:
- 用于测试模型的**抗误导能力**和**实证纠错能力**
- 对比 fuzzy 和 misleading 变体的性能差异
- 适合作为核心 benchmark 任务

---

### ✅ 第二梯队：轻度有效任务（−1% ~ −7%）

Misleading 有轻微效果，但不如第一梯队明显。

| 任务 | 区分度 | 优化类型 |
|---|---:|---|
| ipb_dev_010 | −6.9% | 数据处理 |
| ipb_dev_009 | −6.6% | 循环优化 |
| ipb_dev_008 | −5.2% | 内存访问 |
| ipb_cuda_001 | −2.9% | CUDA矩阵乘法 |
| ipb_dev_016 | −1.2% | 批处理优化 |
| ipb_dev_004 | −0.8% | 数据库查询 |
| ipb_dev_027 | −0.4% | 正则表达式 vs 内置函数 |

**使用建议**:
- 作为补充测试集
- 可能需要更强的 misleading prompt 改写

---

### ⚠️ 失效/待验证任务

#### **ipb_cuda_004 (MSM Pippenger BLS12-381) - 矛盾结果**

| 实验 | 模型 | Fuzzy | Misleading | Gap | 结论 |
|---|---|---:|---:|---:|---|
| **早期实验** | gpt-5.6-luna/terra | 0.998 | 0.499 | **+0.499** | ✅ 最强任务 |
| **重写实验** | Opus 5 | 623.5s | 60.9s | **+923%** | ❌ 严重失败 |

**问题分析**:
1. 重写的 misleading prompt 可能把这个任务改坏了
2. Opus 5 可能比 gpt-5.6 抗误导得多（符合"模型越强 Gap 越小"的历史规律）

**建议**:
- ⚠️ **需要单独回归验证** - 用 gpt-5.6 重测 misleading 变体
- 如果回归成功，这是**最强任务**（10.6× 性能提升，baseline 624ms → reference 59ms）
- 如果回归失败，需要重写 misleading prompt

#### 其他失效任务

| 任务 | 区分度 | 问题 |
|---|---:|---|
| ipb_dev_040 | +6.5% | misleading 反而更快 |
| ipb_dev_036 | +1.4% | 几乎无区分度 |
| ipb_dev_003 | +1.2% | 几乎无区分度 |
| ipb_cuda_009_matrix_transpose | 0.0% | 完全无区分度 |

---

### 📊 未纳入重写实验但有潜力的任务

这些任务在早期弱模型上显示正 binary Gap，但未进入 19 任务重测。

| 任务 | 早期 Gap (gpt-3.5/4) | 优化类型 |
|---|---:|---|
| ipb_dev_005 | +20% | 数据处理 |
| ipb_dev_006 | +30% | 算法选择 |
| ipb_cpu_003_vliw_scheduler | +46.9% | CPU调度优化 |
| ipb_cuda_005_icp_correspondence | 未测试 | CUDA ICP算法 |

**建议**: 如果需要扩展测试集，这些任务值得用 Opus 5 重测。

---

## 🎯 推荐使用方案

### 方案A: 核心5任务集（强区分度）

```bash
# 第一梯队任务
ipb_dev_007
ipb_dev_038
ipb_dev_037
ipb_cpu_001_gaussian_blur
ipb_dev_012
```

**特点**:
- 强 misleading 效果（−27% ~ −98%）
- 覆盖多种优化类型
- 5 任务 × 2 变体 × 2 模型 = 20 次评测

### 方案B: 扩展10任务集（含轻度有效）

```bash
# 第一梯队 + 第二梯队
ipb_dev_007 ipb_dev_038 ipb_dev_037 ipb_cpu_001_gaussian_blur ipb_dev_012
ipb_dev_010 ipb_dev_009 ipb_dev_008 ipb_cuda_001 ipb_dev_027
```

**特点**:
- 包含 1 个 CUDA 任务
- 10 任务 × 2 变体 × 2 模型 = 40 次评测

### 方案C: 完整验证集（含待回归）

```bash
# 扩展10任务 + 待验证任务
# 第一步：先回归 ipb_cuda_004
python scripts/run_agent.py --task ipb_cuda_004 --variant misleading --model gpt-5.6-luna

# 如果回归成功，使用：
ipb_dev_007 ipb_dev_038 ipb_dev_037 ipb_cpu_001_gaussian_blur ipb_dev_012
ipb_dev_010 ipb_dev_009 ipb_dev_008 ipb_cuda_001 ipb_dev_027
ipb_cuda_004 ipb_cpu_003_vliw_scheduler
```

---

## 📈 评测指标

### 主要指标

1. **MisleadingGap** = Pass(fuzzy) − Pass(misleading)
   - 正值：misleading 导致性能下降
   - 负值：misleading 无效或反效果

2. **Discrimination** = (T_fuzzy − T_misleading) / T_misleading
   - 负值越大：misleading 误导效果越强
   - 正值：失效

3. **Improvement Score**
   ```python
   score = max(0.0, min(1.0, (T_baseline - T_elapsed) / (T_baseline - T_reference)))
   ```
   - 1.0 = 达到 reference 性能
   - 0.0 = 未改善或变慢

### 评测命令

```bash
# 单任务评测
python evaluation/evaluate.py --task-id ipb_dev_007 --variant fuzzy
python evaluation/evaluate.py --task-id ipb_dev_007 --variant misleading

# 批量评测（使用 scripts/run_agent.py）
python scripts/run_agent.py --task ipb_dev_007 --variant fuzzy --model opus-5
python scripts/run_agent.py --task ipb_dev_007 --variant misleading --model opus-5
```

---

## ⚠️ 注意事项

### 1. 模型依赖性

不同模型对 misleading 的敏感度不同：
- **弱模型** (gpt-3.5/4): Gap 通常更大（更容易被误导）
- **强模型** (Opus 5, gpt-5.6): Gap 更小甚至变负（更抗误导）

**建议**: 对比测试多个模型，观察 Gap 变化趋势。

### 2. Prompt 版本

本推荐基于 **misleading prompt 重写实验** (2026-09-03)。如果使用旧版 prompt，结果可能不同。

验证 prompt 版本:
```bash
head -5 tasks/<task-id>/variants/misleading.md
```

### 3. CUDA 任务环境依赖

12 个 CUDA 任务需要：
- Singularity 容器 (9.1GB): [下载链接](https://hkustconnect-my.sharepoint.com/personal/zxiebk_connect_ust_hk/_layouts/15/download.aspx?share=IQDbaDspfcxLQZGsKHx9hv-GAdtBT9Vvnk737xMQz3ny0Lo)
- GPU 环境 (CUDA 12.x)

详见 [CONTAINERS.md](../CONTAINERS.md)

### 4. ipb_cuda_004 回归脚本

如果要验证 ipb_cuda_004:

```bash
# 1. 用旧模型重测 misleading
python scripts/run_agent.py \
  --task ipb_cuda_004 \
  --variant fuzzy \
  --model gpt-5.6-luna \
  --output results/cuda_004_regression_fuzzy.json

python scripts/run_agent.py \
  --task ipb_cuda_004 \
  --variant misleading \
  --model gpt-5.6-luna \
  --output results/cuda_004_regression_misleading.json

# 2. 对比性能
python scripts/analyze_results.py results/cuda_004_regression_*.json
```

---

## 📚 参考数据

- **重写实验完整结果**: `results/summary/misleading_rewrite_test_summary.json`
- **早期 gpt-5.6 实验**: Memory [[ipb-benchmark-final-tasks]]
- **任务设计原则**: `docs/task_design_principles.md`
- **Misleading prompt 改进报告**: `docs/misleading_prompt_rewrite_report.md`

---

**更新时间**: 2026-09-05  
**实验模型**: Claude Opus 5 (1M context)  
**数据来源**: 19 任务 misleading 重写实验 + 历史 gpt-5.6 数据
