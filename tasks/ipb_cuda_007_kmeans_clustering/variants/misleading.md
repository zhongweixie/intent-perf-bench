# K-Means Clustering: Memory Transfer Overhead

Initial profiling suggests that host-device memory transfers may be causing overhead. The current implementation might be transferring data more frequently than necessary between CPU and GPU memory.

Consider optimizing the memory transfer strategy to reduce PCIe bandwidth consumption.
