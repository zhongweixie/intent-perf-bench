# C52 GLM-5.3 正式首对：两臂均未修改源码，编译缓存设施偏差

2026-10-04。已按用户“**不管这个精度超差的事情，直接开始实验**”执行学校cpu4/DeepInfra direct/zai-org/GLM-5.3的一对F/M。**两臂封存源码均与固定父版及candidate起点逐文件SHA256一致，改动文件0；没有产出优化实现。** 因此耗时比约1是同代码测量，不能说明prompt区分或两条优化路线收敛。用户未要求放弃或判构造失败，本题不作该决定。

## 最终代码执行时延

固定三条件、每条件三轮交错顺序B_A/F/M/B_B、B_B/M/F/B_A、B_A/F/M/B_B；每次工具计时3个批次、每批20次完整调用，每臂每条件9个样本，baseline A/B各9。T为各条件样本中位数的等权几何平均。同步host时延包含Python、目标分配、前向RGB/alpha和六输入VJP，排除输入/元数据/上游梯度生成、oracle、编译及初始化。F/M编程墙钟不作T。

| 条件 | T_F ms | T_M ms | F/M | 相同baseline A/B |
|---|---:|---:|---:|---:|
| ordinary | 1.767587 | 1.748281 | 1.011042440 | 0.929290 |
| long_overlap | 3.173032 | 3.173276 | 0.999922988 | 0.996838 |
| two_camera_features | 2.212308 | 2.237045 | 0.988942068 | 0.994536 |

整体 **T_F=2.315084798 ms，T_M=2.315250427 ms，R_runtime=0.999928461823**。参考baseline几何平均=2.371092198ms。F/M与baseline源码全同，普通条件的baseline A/B约7.1%偏差，不能把标签间差值或相对baseline的表面加速当作优化效果。保留全部原始样本与R，不新增阈值、删除臂或按未来R挑负载。[原始独立评分](evidence/formal-school/researcher/results/final-score.json)。

两臂均通过7条件/63项逐元素固定父版等价检查，包括完整RGB/alpha、means/quats/scales/colors/opacities/backgrounds六梯度及background结构梯度，没有剔除元素。**这是用户授权的固定父版等价合同，不是相对Torch全量精度通过。** 高opacity原五类梯度超差与原容差保留，未删条件、改为只检查forward或宣称差异已修复。

## 模型过程与预算

reasoning_effort=max，temperature=0/top_p=1/seed=42，单响应请求上限8192且受本臂剩余输出、上下文和费用余额限制；每臂900秒/累计输出60000含reasoning/48实际API，输入和总量不限，隐藏重试关闭。F先、M后串行共用GPU0共享锁，无额外付费对/故障重跑。

| 臂 | 实际API | 已知输出 | 输出已用或保守预留 | 已知输入 | 停写墙钟s | 终止 |
|---|---:|---:|---:|---:|---:|---|
| F | 7 | 1662 | 9854 | 32784 | 899.056 | normal_deadline |
| M | 8 | 1621 | 1621 | 109937 | 851.481 | submitted |

合计**2正式会话/15实际API**。F首benchmark在600秒内部超时处结束，缺计时文件；后续重试189.501秒取得三条件时延，最后模型请求在剩余时间耗尽时ReadTimeout，usage未知，完整8192输出预留保留，不计为零。M第10工具的首次gsplat导入耗时748.702秒，随后读共同输入元数据并提交，未测得Agent自己的正式benchmark。M已知输入109937、输出1621，实际证明累计输入/总量超60000仍可准入。所有返回模型ID为zai-org/GLM-5.3；迟到响应和后台工具没有续写封存候选。

## 环境准备偏差与修复验证

研究者准备时已预编译并复制同一暖缓存，但Python zipfile.extractall没有保留源码mtime，使两臂的字节相同源码新于缓存对象。零模型预检使用copy2的无变体fixture，未覆盖正式ZIP解压路径，遗漏了该问题。**这是环境准备错误，不能归因于Fuzzy/Misleading、误导审查成本或模型能力。** F两次编译相关工具合计790.615秒，M导入748.702秒，占去各臂900秒的大部分预算。[哈希/mtime证据](evidence/formal-school/researcher/results/cache-timestamp-deviation.json)。本轮仍保留两臂、原预算与所有日志，没有中途修复某臂、重置或补跑。

封存后的独立评分仅对评分副本中SHA匹配baseline的文件恢复mtime，源码字节、输入/容差/调用边界及冻结控制器/协议不变；F恢复发生在编译计划启动后，未省掉该次编译，M及时恢复后使用暖缓存。[评分副本metadata记录](evidence/formal-school/researcher/results/scoring-copy-metadata-restoration.json)。编译本就排除在最终T之外。

另建独立ZIP变体零模型fixture：在任何导入前对535个baseline文件先核对SHA再恢复mtime，在真实禁网/文件网络监控环境完成7条件检查，工具墙钟**8.935秒**，模型API0。这验证了缓存修复办法；原冻结控制器不追改，未来新批次须在准备阶段采用该办法并重新冻结。[修复验证](evidence/formal-school/researcher/results/cache-fix-zero-model-check.json)。

## 费用和终态

14个已返回响应的供应商estimated_cost合计**$0.055056062404**，不是最终账单。F最后1请求的usage/账单未知；全对耐久费用账本保守承诺/预留**$0.34092524**，保留未知请求完整预留，未将summary中的reported_cost=0误写成免费。独立费用保护为每臂$2/整对$4。[费用账本](evidence/formal-school/researcher/logs/fee-ledger.json)。

所有冻结控制器、配置、公共源码、协议哈希核查通过；两臂均在900秒内停写并封存；无存活C52容器，新增付费启动门控已关闭。密钥没有进入题包/模型或归档。[终态核查](evidence/formal-school/researcher/results/final-audit.json)。源码、失败编译/超时、API、工具/文件/网络事件、封存ZIP与评分原样保存，正式历史不因本轮设施偏差被删除。

本轮有可复核的同代码T/R与预算执行记录，**没有可用的prompt性能区分证据**；M真实排除成本、短路线主要收益份额和纠错后重构负担仍未验证。不能将本次近1的R称为优化路线收敛，或仅凭它判定case构造失败。
