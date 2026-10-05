# C52：缓存修复后的第二对正式实验

2026-10-04。按用户“修复这个问题并重启一次实验”另登记一对学校cpu4/GPU0/DeepInfra direct/zai-org/GLM-5.3 F/M。原首对2会话/15API及设施偏差完整保留，本轮独立目录`formal-r2`、会话和费用账本，无自动第三对或故障补跑。

## 修复与真实启动验证

ZIP解压后、任何gsplat导入前核对每个文件SHA256，仅对与固定baseline相同的535个gsplat文件恢复原始mtime。真实修改保留新mtime，正常编译。独立负对照验证修改过的CUDA源码和mtime均不会被恢复。封存后独立评分副本采用同样规则，不改变源码字节或跳过改动代码的编译。

新批共同源码/工具/配置/两份题面与首对逐文件相同；原7条件输入及固定父版全量oracle二进制逐文件SHA一致，未重新生成或改负载/容差。高opacity相对Torch的原超差及用户精度门控豁免保留，合同仍为固定父版全量等价，不宣称Torch全量精度通过。

预算、实际禁网/文件网络监控、只读边界、零梯度负对照、三限硬截止停写封存与监控丢失停机均零模型验证通过。重新冻结后，在**两个实际正式注册ZIP启动目录**分别完成7条件全量检查和benchmark，F 16.918s、M 17.399s；各43个.o/.so编译对象SHA和mtime保持不变，确认无重编译。两臂相同地保留预检结果供本轮工具反馈。证据：[真实启动路径验证](evidence/formal-r2-school/researcher/results/real-launch-validation.json)、[修改源码负对照](evidence/formal-r2-school/researcher/results/timestamp-changed-source-negative.json)。

## 正式过程与封存代码

F先、M后，共享GPU0锁串行；reasoning=max、temperature=0/top_p=1/seed=42，单次请求8192输出上限按剩余输出/上下文/费用动态缩小。每臂900秒/累计输出60000含reasoning/48实际API，输入/总量不限、隐藏重试关闭；从首请求计时，包含模型等待及调查/编辑/正常编译/检查。提前提交即封存，无改善或变慢同样保留。

| 臂 | 相对baseline改动文件 | 实际API | 确认输入 | 确认输出 | 输出已用/保守预留 | 停写墙钟s | 终止 |
|---|---:|---:|---:|---:|---:|---:|---|
| F | 1 | 21 | 590874 | 24259 | 24259 | 693.139 | submitted |
| M | 2 | 31 | 1190322 | 35334 | 35334 | 587.130 | spend_cap_snapshot |

本轮合计**2正式会话/52实际API**。源码审查、改动解释及其限制见[封存源码审查](evidence/formal-r2-source-review.json)。两臂均产出调用层优化，M另将反向16×16 tile拆为四个8×8 CTA；源码不同且均通过固定合同完整检查。整体M快约2.18%，但条件间有取舍：长交叠M快约20.18%，双相机特征F快约14.50%，普通条件接近。单对及同代码baseline波动不足以证明prompt因果。

F在693.139秒提前提交。M在587.130秒触及每臂$2的**保守费用准入**保护，下一请求被拒、未计入实际API；最终provider估价只有$0.255627123565，不表示已扣费$2。原clock的通用disposition写作interrupted_failure，summary的明确session_kind/termination_reason为spend_cap_snapshot，按原冻结规则合法评分。M最后改动脚本先写完整反向CTA补丁，随后前向匹配断言失败；末尾grep使shell返回0，最终只保留反向改动，模型停止前未验证它。独立评分已编译该封存版本并全量通过，未改源码或取回较早中间版本。

## 独立完整检查与计时

完整RGB/alpha、means/quats/scales/colors/opacities/backgrounds六输入梯度、background结构逐元素检查，每臂7条件/63项，未剔除元素。评分有效情况：F=True，M=True；主比较完整语义审查通过=True。若错误/缺失/服务或语义合同失败，该臂T及成对R=null；原评分原样保留，不删臂或追改合同。登记域为通道3/5、tile16及固定相机模式；两包装的未执行其他通道padding分支不能视为完整上游API兼容证明，源码审查单列该限制，未事后新增域或判无效规则。

计时仍为完整host同步前向+六输入VJP，包含Python、目标分配/状态和完整梯度，排除编译/初始化、输入/meta/上游梯度生成及oracle。三条件等权几何平均，3轮baseline A/F/M/B、B/M/F/A、A/F/M/B交错，每臂每条件9批次样本；T指产出代码执行时延，不是Agent墙钟。

| 条件 | F ms | M ms | F/M | 同代码baseline A/B |
|---|---:|---:|---:|---:|
| ordinary | 0.530792912 | 0.532269897 | 0.997225121 | 0.952312411 |
| long_overlap | 3.106196318 | 2.479232522 | 1.252886242 | 1.002353538 |
| two_camera_features | 0.468264427 | 0.547655998 | 0.855033870 | 1.088296313 |

**主T_F=0.917378155ms，T_M=0.897399186ms，R_runtime=1.022263190**。R<1表示F产出更快，R>1表示M产出更快。原始结果：[独立评分](evidence/formal-r2-school/researcher/results/final-score.json)。本轮只是单对探索结果，不据此证明prompt因果、不新增R门槛或判case放弃/构造失败。

本轮同一交错baseline的T=2.307671634ms，F/M分别约2.516×/2.572×。相同baseline A/B在ordinary偏差约4.77%、two_camera_features约8.83%，全部样本保留。F/M包装不完全相同，M额外CUDA改动的独立收益份额未用同包装交换CUDA版本的对照验证；不能把全部时延差归因于单一CUDA改动，也不能把两臂整体提速当作prompt区分已成立。

## 费用与终态

已返回响应provider estimated_cost合计**$0.408317247878**，与最终账单区分。usage未知请求0次，完整保守输出/费用预留保留；本轮耐久费用账本承诺/预留上界**$2.88117000**，独立保护每臂$2/整对$4。原首对已知估价$0.055056062404、1请求未知及$0.34092524保守预留另列，未当作免费或吞并到新批。

两批冻结控制器/协议哈希保持，原公共源码/题面一致；两臂三限内停写封存、无存活C52容器，新增付费门控关闭。[终态审计](evidence/formal-r2-school/researcher/results/final-audit.json)。保留实际API/工具/文件/网络事件、失败或超时、完整封存ZIP和原始评分，密钥未进入题包/模型/归档。
