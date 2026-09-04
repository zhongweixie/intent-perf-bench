# Exact Variant

`icp_correspondence()` 在大点云 ICP correspondence step 上性能不足。目标是保留 KD-tree 已由 harness 构建且只上传一次的约束、最近邻阈值语义、H/error/count 输出以及 stream 接口。请分析 GPU KD-tree traversal、线程布局、全局内存、归约和同步，并自行选择优化路径；禁止修改 harness、KD-tree 数据或 Makefile。

**代码风格要求**：保持代码可读性，不要删除所有空格或压缩成单行。在 `__restrict__`、`__shared__` 等 CUDA 关键字、指针声明符、运算符周围保持标准空格。nvcc 编译器要求 `__restrict__` 前后必须有空格。
