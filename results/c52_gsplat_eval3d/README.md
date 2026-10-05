# C52 实验结果

这里只保留最终报告、评分原始数据、实际题面、预算/API/终态摘要和精确封存的最终源码；制作日志、探针、模型对话、编译/调试 trace 不在发布包内。六个有效对与最初 DeepSeek 接口失败结果均保留。

| 实验 | M版本 | F ms | M ms | R=T_F/T_M |
| --- | --- | ---: | ---: | ---: |
| [glm53-pair1](glm53-pair1/score.json) | M1 | 2.315084798 | 2.315250427 | 0.999928462 |
| [glm53-pair2](glm53-pair2/score.json) | M1 | 0.917378155 | 0.897399186 | 1.022263190 |
| [glm53-m2-pair1](glm53-m2-pair1/score.json) | M2 | 0.773067811 | 0.860060340 | 0.898852993 |
| [glm53-m2-pair2](glm53-m2-pair2/score.json) | M2 | 0.805152045 | 2.288378403 | 0.351843928 |
| [deepseek41-pair1](deepseek41-pair1/score.json) | M2 | 0.618588331 | 2.318160762 | 0.266844449 |
| [deepseek41-pair2](deepseek41-pair2/score.json) | M2 | 2.378054888 | 2.170093604 | 1.095830560 |

R<1 表示 F 产出代码更快；R>1 表示 M 更快。主指标是最终代码完整调用时延，编程墙钟只作过程信息。不同模型/版本/控制器批次不合并为一个总体效果。

[最新 DeepSeek 两对报告](deepseek41-two-pair-report.md)、[统计 JSON](deepseek41-two-pair-statistics.json)、[完整汇总](summary.json)。DeepSeek 两对几何平均 R=0.540755307，F/M各胜一对，尚未证明稳定提示因果。初始两对接口失败 R=null，说明和原始结果保留。

每轮 score.json 保留完整63项正确性和三条件交错测量样本；F/M/final-source.zip 是原封存 ZIP，校验值见 summary.json。F/M/prompt.md 是当轮实际给模型的完整题面。历史报告按原文保留，其中提及的准备记录、会话和全量归档仅存于本地研究工作区；本成品发布不附这些中间材料。费用估算及设施偏差以原报告为准，摘要中的 API/预算不冒充最终账单。

复核最终代码可使用 [C52 评分入口](../../tasks/c52_gsplat_eval3d/README.md)，用 --candidate 指向对应 final-source.zip。报告中的数学/精度结论只适用于注册合同。公开分支不向被测 Agent 展示本 results 目录。
