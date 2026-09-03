# 关键实验数据

本目录包含19个负区分度任务重写测试的原始结果数据。

## 数据来源

从1112个历史测试结果中提取的最新测试数据（2026-09-02至2026-09-03）：
- **17个任务** 完成了完整测试（fuzzy + misleading）
- **2个任务** 缺失数据（ipb_dev_032, ipb_dev_041）
- **34个JSON文件** = 17任务 × 2变体

## 文件命名规则

```
{task_name}_{variant}_run{timestamp}.json
```

例如：
- `ipb_dev_007_fuzzy_run1788406305.json` - dev_007任务的fuzzy变体测试
- `ipb_dev_007_misleading_run1788408040.json` - dev_007任务的misleading变体测试

## JSON数据结构

每个文件包含：
```json
{
  "turns": 10,              // AI轮数
  "elapsed_time": 0.4293,   // 优化后代码运行时间（秒）
  "passed": true,           // 是否通过测试
  "turns_to_real_target": 2,// 找到真正瓶颈的轮数
  "trajectory": [...],      // 完整对话轨迹
  "benchmark_output": "..." // benchmark运行输出
}
```

## 区分度计算

**区分度 = (Fuzzy时间 - Misleading时间) / Misleading时间 × 100%**

- **负值**（< 0%）：成功误导，Misleading使优化更慢
- **正值**（> 0%）：失败，Misleading反而帮助了优化
- **接近0**：无显著影响

## 测试结果汇总

详见 `../summary/misleading_rewrite_test_summary.json`
