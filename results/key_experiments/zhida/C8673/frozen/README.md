# C8673 Codex：700 秒冻结归档

2026-10-06 按用户确认冻结。模型 gpt-6.1-sol / medium，700 有效秒，48 响应 guard，40k 生成 token，1.25M 累计 token，两轮 Fuzzy / flatten_hint 配对。两轮均正确，Fuzzy/flatten 延迟比 0.724 / 0.809。冻结仅限此配置的两轮证据。

先阅读 `C8673_Codex_700s_两轮验收.md`；`FREEZE.json` 是冻结配置与成绩。`round1/round2` 包含提示词、预算、benchmark、最终评分、操作轨迹、冻结提交 JSON；`submitted_source/` 才是最终解，`initial_public/` 是 solver 初始可见文件。

Codex 解题进程在本地电脑运行，GPU 性能测试在 songcpu4 完成；此目录是研究者验收归档，尚不是在服务器上一条命令启动 Codex 的独立发行包。`controller_snapshot/` 保存调用器实现用于审查，使用需要本地 Codex app-server 与已登录会话。原 candidate8673-clearer-v4 的旧 launch.py 是旧 API 实验入口，不是本次 Codex 入口。

`grader_snapshot/` 保存服务器原任务的评分器、映射和沙箱；只供研究者审查，不暴露给 solver。controller 动态工具仅提供初始公共源码与合同。reference_evaluation.json 只有参考成绩；本目录不分发参考答案源码、API key 或登录凭据。

后续复验须使用新目录，保留当前两轮及所有正常反向样本；不覆盖本归档。
