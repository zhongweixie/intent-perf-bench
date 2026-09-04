# IPB_DEV_004 - pandas DataFrame.apply() Anti-pattern

## 任务概述

**场景**: 数据分析管道中的指标计算模块性能回归  
**回归类型**: 将向量化操作重构为 `DataFrame.apply()` 的行遍历调用  
**Speedup**: 4.9x (Stage 3: 297x)  
**难度等级**: 中等

## 性能指标

| 版本 | Total Time | Stage 3 Time | Speedup |
|------|-----------|--------------|---------|
| Regressed (20a477d) | 0.86s | 0.68s | 1.0x |
| Baseline (e405d44) | 0.18s | 0.0023s | 4.9x |

**Stage 3 Speedup**: 0.68s → 0.0023s = **297x**

## 回归根因

### 修改前（Baseline - 快速）
```python
def calculate_derived_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    
    # Vectorized calculations - much faster than apply()
    df['total_revenue'] = df['amount'] * df['quantity']
    df['discounted_amount'] = df['total_revenue'] * (1 - df['discount_rate'])
    
    # Profit margin calculation
    cost_estimate = df['total_revenue'] * 0.6
    df['profit_margin'] = np.where(
        df['total_revenue'] > 0,
        (df['total_revenue'] - cost_estimate) / df['total_revenue'],
        0.0
    )
    
    return df
```

### 修改后（Regressed - 慢）
```python
def calculate_derived_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    
    # Refactored to use helper methods for better code organization
    df['total_revenue'] = df.apply(self._calculate_revenue, axis=1)
    df['discounted_amount'] = df.apply(self._calculate_discounted, axis=1)
    df['profit_margin'] = df.apply(self._calculate_margin, axis=1)
    
    return df

def _calculate_revenue(self, row):
    return row['amount'] * row['quantity']

def _calculate_discounted(self, row):
    return row['total_revenue'] * (1 - row['discount_rate'])

def _calculate_margin(self, row):
    if row['total_revenue'] == 0:
        return 0.0
    cost = row['total_revenue'] * 0.6
    return (row['total_revenue'] - cost) / row['total_revenue']
```

**问题**: `DataFrame.apply(axis=1)` 对每一行调用 Python 函数，失去了 NumPy/pandas 的向量化优势。

## 任务设计参数

### 搜索空间
- **模块总数**: 6 (loader / validator / aggregator / reporter / run_analytics / benchmarks)
- **函数总数**: ~25
- **目标模块**: `analytics/aggregator.py`
- **目标函数**: `calculate_derived_metrics()`

### 证据间接性
- **Exact**: profiler 指向 `aggregator.py:19(calculate_derived_metrics)` 和帮助方法 `_calculate_*`
- **Fuzzy**: 只有 benchmark 输出（Stage 3 慢）
- **Misleading**: 强调 Stage 1 (data loading) I/O 时间
- **Target-known**: 直接告知 `aggregator.py` 的 `calculate_derived_metrics()` 函数

### 误导方向
- **错误瓶颈**: Stage 1 (data loading) — 0.16-0.17s
- **真实瓶颈**: Stage 3 (metrics calculation) — 0.68s
- **误导可信度**: 中等（I/O 占 19%，看起来重要但实际是预期值）

## 变体设计

### Exact
- 提供完整证据：profiler + benchmark + git.log
- Profiler 显示 `aggregator.py` 和帮助方法占 69% 时间
- 不暴露具体的 apply() 问题

### Fuzzy
- 只提供 benchmark + git.log
- Benchmark 显示 Stage 3 慢但不指明具体模块

### Misleading
- 提供 benchmark + git.log
- 用户注释强调 Stage 1 I/O 时间（0.16s）
- 暗示应优化数据加载性能

### Target-known
- 明确指出问题在 `aggregator.py` 的 `calculate_derived_metrics()`
- 提供 git.log 供参考

## 评测指标

### 成功标准
- `passed = True`: benchmark 输出包含 "✓ PASS" 且返回码为 0
- `modified_causal_file = True`: diff 修改了 `analytics/aggregator.py`

### 过程指标
- `turns_to_real_target`: 首次接触 `aggregator.py` 的轮次
- `profiled`: 是否运行了 profiling（Exact 变体相关）
- `wrong_dir_persistence`: 在证据表明 I/O 非瓶颈后仍继续优化 loader

## 预期区分度

基于任务难度公式：
```
难度 = 搜索空间(中) × 证据间接性(中) × 误导可信度(中等)
```

**预期成功率**:
- Exact: 60-70%（有 profiler 指向模块）
- Fuzzy: 50-60%（需要自己 profile）
- Misleading: 30-40%（I/O 方向有一定可信度）
- Target-known: 70-80%（已知目标模块）

**预期 Gap**:
- FuzzyGap: +5-10%
- MisleadingGap: +20-30%

## 与 ipb_dev_003 对比

| 维度 | ipb_dev_003 | ipb_dev_004 |
|------|-------------|-------------|
| 反模式 | iterrows() | apply(axis=1) |
| Speedup | 1451x | 297x |
| 搜索空间 | 5 模块 | 6 模块 |
| 误导占比 | ~50% (Export) | ~19% (I/O) |
| 证据间接性 | 中（profiler → module） | 中（profiler → module + helpers） |
| 预期 MisleadingGap | +25% (已验证) | +20-30% (待验证) |

## 构建状态

- ✅ Workspace 结构完成
- ✅ Baseline / Regressed 版本创建
- ✅ Git 历史生成
- ✅ 证据文件（profiler / benchmark / git.log）
- ✅ 系统提示（4 个变体）
- ✅ 变体描述（4 个 variants/*.md）
- ✅ task_config.json
- ✅ run_agent.py 集成
- ✅ 基准测试验证（Regressed: FAIL, Baseline: PASS）

**下一步**: 运行测试验证区分度
