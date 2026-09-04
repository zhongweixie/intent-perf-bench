# Fuzzy Variant

固定场景的光线渲染结果正确，但每帧耗时过高。分析每条 primary ray 的场景查询路径、三角形测试数量和空间访问局部性。不得改变最近交点语义或 checksum 行为。
