#include <stdio.h>
#include <cuda_runtime.h>

int main() {
    int deviceCount = 0;
    cudaError_t err = cudaGetDeviceCount(&deviceCount);
    if (err != cudaSuccess) {
        printf("cudaGetDeviceCount failed: %s\n", cudaGetErrorString(err));
        return 1;
    }
    printf("Found %d CUDA devices\n", deviceCount);
    
    for (int i = 0; i < deviceCount; i++) {
        cudaDeviceProp prop;
        cudaGetDeviceProperties(&prop, i);
        printf("Device %d: %s\n", i, prop.name);
        printf("  Compute capability: %d.%d\n", prop.major, prop.minor);
        printf("  Total memory: %.2f GB\n", prop.totalGlobalMem / (1024.0*1024.0*1024.0));
    }
    
    // 尝试初始化 device 0
    err = cudaSetDevice(0);
    if (err != cudaSuccess) {
        printf("cudaSetDevice(0) failed: %s\n", cudaGetErrorString(err));
        return 1;
    }
    printf("Successfully set device 0\n");
    
    // 尝试分配少量内存
    void* ptr = nullptr;
    err = cudaMalloc(&ptr, 1024);
    if (err != cudaSuccess) {
        printf("cudaMalloc failed: %s\n", cudaGetErrorString(err));
        return 1;
    }
    printf("Successfully allocated 1KB on GPU\n");
    cudaFree(ptr);
    
    return 0;
}
