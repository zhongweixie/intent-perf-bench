# IPB 任务分析与改造文档汇总
**目录**: `/home/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/docs/tmp`  
**更新时间**: 2024-09-02

---

## 📋 文档索引

### 1. **ipb_tasks_status_report.md** ⭐ **最新状态报告**
**生成时间**: 2024-09-02 13:59  
**用途**: 当前所有任务的全面状态总结

**内容**：
- ✅ 可用任务清单（16个）
- 🔒 待重测任务（2个，删除注释后）
- ❌ 已淘汰任务（2个）
- ❓ 未测试任务（1个）
- 📊 区分度分布与 AI 场景覆盖
- 🔧 最近改造工作总结
- 📋 下一步工作计划
- 💡 Tier S/A/B/C 推荐任务集

**适用场景**: 
- 了解当前任务池状态
- 规划下一步测试工作
- 选择 Benchmark 任务组合

---

### 2. **ai4ai_calibration_summary.md** ⭐ **标定数据汇总**
**生成时间**: 2024-09-02 12:17  
**用途**: AI4AI dev 任务的性能标定结果

**内容**：
- 7个 dev 任务的 baseline/current 性能对比
- Speedup 范围: 1.4x - 158x
- 反模式分析（iterrows, 重复join等）
- 优化模式总结（向量化，批量操作）
- 任务优先级推荐

**标定任务**：
- ipb_dev_004 (4.4x)
- ipb_dev_007 (158x!) 
- ipb_dev_008 (6.6x)
- ipb_dev_009 (12.0x)
- ipb_dev_010 (4.6x)
- ipb_dev_037 (5.9x)
- ipb_dev_041 (1.4x)

**适用场景**:
- 查看 dev 任务的性能基准
- 理解优化模式和反模式
- 选择高 speedup 的 AI 任务

---

### 3. **ipb_final_recommendation.md**
**生成时间**: 2024-09-02 04:05  
**用途**: 早期任务推荐方案

**内容**：
- 13个推荐任务清单
- Native vs Dev 任务分类
- 区分度分析
- 淘汰任务理由

**注意**: 部分信息已过时，被 `ipb_tasks_status_report.md` 更新

---

### 4. **ipb_ai4ai_task_analysis.md**
**生成时间**: 2024-09-02 04:05  
**用途**: AI4AI 场景适配性分析

**内容**：
- 25个 dev 任务的 AI 场景评估
- 推荐/不推荐任务分类
- 场景适配建议

**关键发现**：
- 8个高度推荐（训练、推理、数据处理）
- 17个不推荐或缺少 prompt

---

### 5. **ipb_discrimination_analysis_complete.md**
**生成时间**: 2024-09-02 04:05  
**用途**: 区分度完整分析

**内容**：
- Tier 1-4 任务分类
- Fuzzy vs Misleading 性能对比
- 区分度计算方法
- 问题诊断

**注意**: 基础分析文档，后续文档有更新结论

---

### 6. **ipb_updated_decision.md**
**生成时间**: 2024-09-02 04:05  
**用途**: 早期决策文档

**内容**：
- 任务保留/淘汰决策
- 区分度阈值设定

**注意**: 已被最新报告更新

---

### 7. **analyze_dev_tasks.js**
**生成时间**: 2024-09-02 04:05  
**用途**: 自动化分析脚本

**内容**：
- Dev 任务 prompt 扫描脚本
- 用于检测缺失的 fuzzy/misleading prompt

---

## 🎯 推荐阅读顺序

### 快速了解（5分钟）
1. **ipb_tasks_status_report.md** - 查看 Executive Summary 和推荐任务集

### 深入理解（15分钟）
1. **ipb_tasks_status_report.md** - 完整阅读
2. **ai4ai_calibration_summary.md** - 了解性能基准和优化模式

### 全面掌握（30分钟）
1. **ipb_tasks_status_report.md**
2. **ai4ai_calibration_summary.md**
3. **ipb_ai4ai_task_analysis.md** - 了解更多 dev 任务
4. **ipb_discrimination_analysis_complete.md** - 理解区分度分析方法

---

## 📊 关键数据速查

### 任务统计
- **总任务数**: 21
- **可用任务**: 16 (76%)
- **待重测**: 2 (删除注释后)
- **已淘汰**: 2
- **未测试**: 1

### 区分度分布
- **>10x**: 4 tasks (Tier S)
- **5-10x**: 3 tasks (Tier A)
- **3-5x**: 4 tasks (Tier B)
- **<3x**: 5 tasks (Tier C)

### AI场景覆盖
- **AI相关**: 14/16 (88%)
- **通用优化**: 1/16 (6%)
- **未分类**: 1/16 (6%)

---

## 🔧 最近工作（2024-09-02）

### 完成
1. ✅ 删除泄露注释 (ipb_cuda_005_l2norm, ipb_cuda_009_transpose)
2. ✅ 修复 gaussian_blur 正确性问题（禁止精度降级）
3. ✅ 为 7个 dev 任务建立标定路径
4. ✅ 生成完整状态报告

### 待办
1. [ ] 重测删除注释后的两个任务
2. [ ] 强化低区分度任务的 misleading prompt
3. [ ] 测试 Flash Attention（如果环境支持）
4. [ ] 收集完整的 Improvement Score 数据

---

## 📁 相关目录

### 任务工作区
```
/aifs4su/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/tasks/
├── ipb_cpu_001_gaussian_blur/      # 已修复
├── ipb_cuda_005_l2norm_reduction/  # 已删除注释，待重测
├── ipb_cuda_009_matrix_transpose/  # 已删除注释，待重测
├── ipb_dev_004/                    # 已标定
├── ipb_dev_007/                    # 已标定
└── ...
```

### 测试结果
```
/aifs4su/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/results/
├── batch_logs/
├── ipb_*.json
└── remeasure_*.json
```

---

## 💡 使用建议

### 场景 1: 选择 Benchmark 任务
→ 阅读 `ipb_tasks_status_report.md` 的 "最终推荐任务集" 部分

### 场景 2: 了解任务性能基准
→ 阅读 `ai4ai_calibration_summary.md` 的标定结果表格

### 场景 3: 理解任务改造历史
→ 阅读 `ipb_tasks_status_report.md` 的 "最近改造工作" 部分

### 场景 4: 规划下一步工作
→ 阅读 `ipb_tasks_status_report.md` 的 "下一步工作" 部分

### 场景 5: 深入研究区分度问题
→ 阅读 `ipb_discrimination_analysis_complete.md` + `ipb_final_recommendation.md`

---

## 🔗 外部参考

### 诊断报告（未在此目录）
- `/tmp/tier4_diagnosis.md` - Tier 4 任务深度诊断
- `/tmp/three_tasks_reevaluation.md` - 三任务重新评估
- `/tmp/ipb_reform_final_summary.md` - 改造总结

### Git 仓库
- Native tasks: 在各任务的 workspace/.git
- Dev tasks: 在各任务的 workspace/.git

---

## ✅ 文档完整性检查

- [x] 任务状态报告
- [x] 标定数据汇总
- [x] AI场景分析
- [x] 区分度分析
- [x] 推荐方案
- [x] 索引文档（本文件）

**所有核心文档已完成！**

---

## 📞 联系方式

如有疑问，参考：
- 主报告: `ipb_tasks_status_report.md`
- 标定数据: `ai4ai_calibration_summary.md`
- 历史分析: 其他 markdown 文件
