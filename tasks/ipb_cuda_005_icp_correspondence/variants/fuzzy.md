# ICP Correspondence Performance Issue

Our 3D scene understanding pipeline for autonomous driving uses ICP (Iterative Closest Point) correspondence search to align LiDAR point clouds from consecutive frames. This is critical for building accurate 3D maps and tracking objects in real-time.

The point cloud correspondence step is taking far too long on large datasets (10K points per frame). Results are correct but execution time makes the system unsuitable for real-time perception and mapping applications.

Analyze and optimize the CUDA implementation to achieve real-time performance.

Context: Self-driving perception systems must process LiDAR data at 10-20 Hz to maintain accurate localization and object tracking.
