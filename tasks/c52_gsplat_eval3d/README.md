# C52：gsplat 世界空间 3DGS 完整前向与反向

这是可交给 Agent 的成品性能案例。优化 world-space eval3d 的 RGB/特征、alpha 前向及 means/quats/scales/colors/opacities/backgrounds 六类 VJP；保持 global-shutter pinhole、use_hit_distance=False、截断、相机与梯度语义。共同输入/相交元数据固定在调用外。

- workspace/：起始 candidate.py、完整相关 gsplat 源码和 check/bench/profile/submit 工具。
- variants/：最终 Fuzzy 和多角度 Misleading M2；每份是完整实际题面，公共段一致。
- evaluation/：固定父版 oracle、七负载生成器和独立评分入口。
- experiment-budget.json：每臂900秒、累计输出60000含reasoning、48实际API；输入/总usage不限，金额仅记账。
- [实验结果](../../results/c52_gsplat_eval3d/README.md)：报告、评分、最终源码和实际题面。

## 环境与运行

历史实测环境为 Linux、PyTorch 2.9.0+cu128、CUDA开发工具链、RTX A6000 (SM8.6)。需要已有匹配 Torch/CUDA 环境和 nvcc/C++ 编译器；本包带齐 gsplat 与 GLM 头文件，不需要下载上游源码。

从本案例目录运行：

```bash
python -m pip install -r requirements.txt
export TORCH_CUDA_ARCH_LIST=8.6
python evaluation/prepare.py --output .runtime/contract
python evaluation/evaluate.py --output .runtime/baseline-score.json
```

prepare 仅由研究者在首次模型请求前运行：从不可修改的 oracle.zip 生成七条件输入和固定父版全部输出/梯度，写入独立 contract 并记录哈希。它是成品所需的数据生成工具，不是制作过程日志。既有 contract 不覆盖；迁移硬件后生成的数据不冒充历史冻结数据。

评价其他 workspace 或最终 ZIP：

```bash
python evaluation/evaluate.py --candidate /path/to/final-source.zip --contract .runtime/contract --output .runtime/candidate-score.json
```

也可在 workspace 运行 `python tools/case.py check --output ../.runtime/check.json`、`python tools/case.py bench --rounds 3 --output ../.runtime/bench.json` 或 profile。使用其他 contract 时设置 C52_CONTRACT_DIR；指定其他代码目录时设置 C52_TASK_ROOT。compile/input/oracle 不计入 T，所有目标分配、Python、同步、前向和六VJP计入。

## 评测合同

完整检查覆盖七条件/63项，基于固定父版全张量等价，并检查 background 结构梯度；不存在元素掩码。高 opacity 相对 Torch 参考的已知残差按原授权保留，不宣称全部满足 Torch 数学参考。bench 固定 ordinary、long_overlap、two_camera_features，各取完整调用中位数，三项取几何平均。主比较 R=T_F/T_M，无加速或区分度通过阈值。共同交错计时的原始样本见结果 score.json；此便携入口输出单候选 T，配对正式实验仍需外部控制器安排同合同交错测量。

## 接入 Agent

给两臂各复制干净 workspace 和各自一份 variants 题面；先共同预热完整检查与编译，再从首个模型请求开始预算。只有 candidate.py 与 gsplat/可写，其余工具、题面、输入与检查器只读。外部 Agent runner 须实际禁网、执行三限、停止写入并封存；模型 API 在沙箱外调用。不要将 evaluation 的 oracle 或 results 挂给被测 Agent。这里不含模型登录、学校 SSH 或付费启动脚本。

这是独立案例评分入口，未强行接入根 evaluation/evaluate.py 的阈值成功率合同。基线/题面/最终封存代码沿用已完成实验的原字节；本次只做工具路径适配和成品整理，已做静态与CPU接线核查，没有新增GPU或付费实验。历史结果的限制和设施偏差保留在报告。
