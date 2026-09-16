#include <stdio.h>
#include <cuda_runtime.h>

int main() {
    cudaError_t err = cudaSetDevice(0);
    if (err != cudaSuccess) {
        printf("cudaSetDevice failed: %s\n", cudaGetErrorString(err));
        return 1;
    }
    
    // 尝试分配 256 MB
    void* ptr = nullptr;
    size_t size = 256 * 1024 * 1024;
    err = cudaMalloc(&ptr, size);
    if (err != cudaSuccess) {
        printf("cudaMalloc failed: %s (error code: %d)\n", cudaGetErrorString(err), err);
        return 1;
    }
    
    printf("cudaMalloc success: allocated %zu MB\n", size / (1024*1024));
    cudaFree(ptr);
    return 0;
}
