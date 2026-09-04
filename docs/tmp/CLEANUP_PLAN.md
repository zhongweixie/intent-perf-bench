# 文档清理建议 - 2024-09-02

## 📊 当前文档列表 (16个文件)

### ✅ 保留 - 核心文档 (6个)

#### 主文档 (3个)
1. **FINAL_SUMMARY.md** (4.4K, Sep 2 14:41) ⭐ 
   - 最终工作总结
   - 17个任务完整列表
   - 推荐使用方案
   - **必须保留**

2. **IPB_TASKS_FINAL_STATUS.md** (5.5K, Sep 2 14:18) ⭐
   - 完整状态报告
   - 详细分层统计
   - **必须保留**

3. **README.md** (6.1K, Sep 2 14:00) ⭐
   - 文档索引和导航
   - **必须保留**

#### 数据文档 (2个)
4. **ai4ai_calibration_summary.md** (5.4K, Sep 2 12:17)
   - 7个dev任务的标定数据
   - baseline_perf.log 路径
   - **必须保留**

5. **ipb_tasks_status_report.md** (7.6K, Sep 2 13:59)
   - 详细任务状态
   - 包含测试结果和改造记录
   - **必须保留**

#### 分析文档 (1个)
6. **L2NORM_TRANSPOSE_ANALYSIS.md** (3.6K, Sep 2 14:41)
   - l2norm/transpose 不加入的决策依据
   - 基于代码分析的预测
   - **建议保留** (记录决策过程)

---

### ⚠️ 可选保留 - 过程记录 (3个)

7. **WORK_SUMMARY.md** (7.2K, Sep 2 14:01)
   - 第一轮工作总结
   - 内容已包含在 FINAL_SUMMARY 中
   - **可以删除**，但保留有助于追溯历史

8. **WORK_PROGRESS_ROUND2.md** (5.1K, Sep 2 14:16)
   - 第二轮工作进展
   - 内容已包含在 FINAL_SUMMARY 中
   - **可以删除**，但保留有助于追溯历史

9. **STATUS_SNAPSHOT.md** (2.1K, Sep 2 14:28)
   - 快速状态快照
   - 与 FINAL_SUMMARY 重复
   - **可以删除** (信息已在其他文档中)

---

### ❌ 建议删除 - 过时文档 (5个)

10. **ipb_final_recommendation.md** (17K, Sep 2 04:05)
    - 早期推荐（13个任务）
    - 已被 FINAL_SUMMARY 替代
    - **删除**

11. **ipb_discrimination_analysis_complete.md** (14K, Sep 2 04:05)
    - 早期区分度分析
    - 数据已过时
    - **删除**

12. **ipb_ai4ai_task_analysis.md** (24K, Sep 2 04:05)
    - 早期AI场景分析
    - 内容已整合到最终文档
    - **删除**

13. **ipb_updated_decision.md** (7.1K, Sep 2 04:05)
    - 早期决策记录
    - 已被新文档替代
    - **删除**

14. **TEST_PROGRESS.md** (1.5K, Sep 2 14:27)
    - 测试进度记录
    - API失败记录，已在 L2NORM_TRANSPOSE_ANALYSIS 中说明
    - **删除**

---

### 🗑️ 其他文件 (2个)

15. **analyze_dev_tasks.js** (6.5K, Sep 2 04:05)
    - 分析脚本
    - 一次性使用
    - **删除**（或移到 scripts/ 目录）

16. **zh** (68 bytes, Sep 2 15:44)
    - 未知文件
    - **删除**

---

## 🎯 清理方案

### 方案 A: 激进清理（推荐）
**保留 6 个核心文档**

```bash
cd /home/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/docs/tmp

# 删除过时文档 (5个)
rm ipb_final_recommendation.md
rm ipb_discrimination_analysis_complete.md
rm ipb_ai4ai_task_analysis.md
rm ipb_updated_decision.md
rm TEST_PROGRESS.md

# 删除其他 (2个)
rm analyze_dev_tasks.js
rm zh

# 删除重复的快照
rm STATUS_SNAPSHOT.md

# 可选：删除过程记录
rm WORK_SUMMARY.md
rm WORK_PROGRESS_ROUND2.md
```

**结果**: 6个核心文档（如果删除过程记录）或 8个文档（如果保留过程记录）

---

### 方案 B: 保守清理
**保留 9 个文档（含过程记录）**

```bash
cd /home/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/docs/tmp

# 只删除过时文档 (5个)
rm ipb_final_recommendation.md
rm ipb_discrimination_analysis_complete.md
rm ipb_ai4ai_task_analysis.md
rm ipb_updated_decision.md
rm TEST_PROGRESS.md

# 删除其他 (2个)
rm analyze_dev_tasks.js
rm zh

# 保留 STATUS_SNAPSHOT（快速查看）
# 保留 WORK_SUMMARY 和 WORK_PROGRESS_ROUND2（历史追溯）
```

**结果**: 9个文档

---

## 📁 清理后的目录结构

### 核心文档集（方案A推荐）
```
docs/tmp/
├── FINAL_SUMMARY.md                    ⭐ 最终总结
├── IPB_TASKS_FINAL_STATUS.md          ⭐ 完整状态
├── README.md                           ⭐ 文档索引
├── ai4ai_calibration_summary.md        📊 标定数据
├── ipb_tasks_status_report.md          📋 详细状态
└── L2NORM_TRANSPOSE_ANALYSIS.md        📝 决策依据
```

### 如果保留过程记录（方案B）
```
docs/tmp/
├── FINAL_SUMMARY.md                    ⭐ 最终总结
├── IPB_TASKS_FINAL_STATUS.md          ⭐ 完整状态
├── README.md                           ⭐ 文档索引
├── ai4ai_calibration_summary.md        📊 标定数据
├── ipb_tasks_status_report.md          📋 详细状态
├── L2NORM_TRANSPOSE_ANALYSIS.md        📝 决策依据
├── WORK_SUMMARY.md                     📜 第一轮工作
├── WORK_PROGRESS_ROUND2.md             📜 第二轮工作
└── STATUS_SNAPSHOT.md                  📸 快速快照
```

---

## 💡 推荐

**采用方案 A（激进清理）**：
- ✅ 保留 6 个核心文档
- ✅ 删除 10 个过时/重复文档
- ✅ 目录清晰，易于维护
- ✅ 所有关键信息都在 FINAL_SUMMARY 中

**如果需要保留工作历史**：
- 可以将 WORK_SUMMARY 和 WORK_PROGRESS_ROUND2 移到 `docs/archive/`
- 而不是直接删除

---

## 🔧 执行清理

```bash
# 创建备份（可选）
cd /home/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/docs
mkdir -p archive
cp -r tmp archive/tmp_backup_$(date +%Y%m%d)

# 执行方案 A
cd tmp
rm ipb_final_recommendation.md \
   ipb_discrimination_analysis_complete.md \
   ipb_ai4ai_task_analysis.md \
   ipb_updated_decision.md \
   TEST_PROGRESS.md \
   analyze_dev_tasks.js \
   zh \
   STATUS_SNAPSHOT.md \
   WORK_SUMMARY.md \
   WORK_PROGRESS_ROUND2.md

# 验证
ls -lh
```

---

**生成时间**: 2024-09-02 14:50  
**推荐**: 方案 A（保留 6 个核心文档）  
**备份建议**: 移动过时文档到 archive/ 而不是直接删除
