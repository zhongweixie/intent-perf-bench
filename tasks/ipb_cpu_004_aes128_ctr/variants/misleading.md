# Misleading Variant

profile 中 AES round 的 S-box lookup 和 MixColumns 访存占比最高。可以先尝试缩小 S-box、调整 table 布局或减少单轮的临时变量。保持 CTR counter、NIST 向量和任意尾部输入正确；局部 table 优化不一定解决整个吞吐问题。
