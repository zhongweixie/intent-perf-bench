#include <cuda_runtime.h>
#include <cstdio>

int main() {
    // Try to initialize CUDA runtime
    int deviceCount = 0;
    cudaError_t err = cudaGetDeviceCount(&deviceCount);
    printf("cudaGetDeviceCount: %s\n", cudaGetErrorString(err));
    printf("Device count: %d\n", deviceCount);
    
    if (deviceCount > 0) {
        err = cudaSetDevice(0);
        printf("cudaSetDevice(0): %s\n", cudaGetErrorString(err));
        
        // Try a simple kernel launch to initialize
        err = cudaDeviceSynchronize();
        printf("cudaDeviceSynchronize: %s\n", cudaGetErrorString(err));
        
        // Now try malloc
        void* ptr = nullptr;
        err = cudaMalloc(&ptr, 256 * 1024 * 1024);
        printf("cudaMalloc(256MB): %s\n", cudaGetErrorString(err));
        if (err == cudaSuccess) {
            cudaFree(ptr);
        }
    }
    
    return 0;
}
