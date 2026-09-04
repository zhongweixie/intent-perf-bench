# Exact Variant

当前 `Intersect()` 对每条 ray 线性扫描全部 4096 个三角形，导致渲染开销为 rays×triangles。请在 `Build()` 中构造空间加速结构，并在 `Intersect()` 中剪枝遍历；必须返回最近交点并保持 checksum 完全一致。
