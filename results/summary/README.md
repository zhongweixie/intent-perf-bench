# 测试结果汇总

本目录包含19个负区分度任务重写测试的汇总数据。

## 文件说明

### misleading_rewrite_test_summary.json
完整的测试结果数据，包含：
- 17个完成测试的任务
- 每个任务的fuzzy和misleading变体指标
- 计算的区分度

### 数据格式

```json
{
  "experiment": "misleading_prompt_rewrite",
  "tasks_tested": 17,
  "results": [
    {
      "task": "ipb_dev_007",
      "fuzzy": {
        "turns": 9,
        "elapsed_time": 0.4293,
        "passed": true,
        "turns_to_real_target": 2
      },
      "misleading": {
        "turns": 28,
        "elapsed_time": 28.7925,
        "passed": false,
        "turns_to_real_target": null
      },
      "discrimination": -98.5
    }
  ]
}
```

## 区分度说明

**区分度** = (Fuzzy时间 - Misleading时间) / Misleading时间 × 100%

- **负区分度**（< 0%）：成功误导，misleading使模型的优化更慢
- **正区分度**（> 0%）：失败，misleading反而帮助了模型
- **零区分度**（≈ 0%）：无显著影响

## 最终统计

- **成功率**: 47.1% (8/17)
- **超级成功**: 3个（区分度 < -50%）
- **中等成功**: 5个（-50% < 区分度 < -5%）
- **零影响**: 7个（-5% ≤ 区分度 ≤ 5%）
- **失败**: 2个（区分度 > 5%）

详细分析请运行 `scripts/generate_final_summary.py`
