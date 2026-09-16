#include <cuda_runtime.h>
#include <stdio.h>

int main() {
    int deviceCount = 0;
    cudaError_t err = cudaGetDeviceCount(&deviceCount);
    printf("cudaGetDeviceCount: %s\n", cudaGetErrorString(err));
    printf("Device count: %d\n", deviceCount);

    if (deviceCount > 0) {
        cudaDeviceProp prop;
        cudaGetDeviceProperties(&prop, 0);
        printf("Device 0: %s\n", prop.name);
        printf("Compute capability: %d.%d\n", prop.major, prop.minor);

        // 尝试分配一小块内存
        void* ptr = nullptr;
        err = cudaMalloc(&ptr, 1024);
        printf("cudaMalloc(1KB): %s\n", cudaGetErrorString(err));
        if (err == cudaSuccess) {
            cudaFree(ptr);
            printf("Small allocation succeeded\n");

            // 尝试分配一个较大的块 (256MB)
            err = cudaMalloc(&ptr, 256ULL * 1024 * 1024);
            printf("cudaMalloc(256MB): %s\n", cudaGetErrorString(err));
            if (err == cudaSuccess) {
                cudaFree(ptr);
                printf("Large allocation succeeded\n");
            }
        }
    }

    return 0;
}
