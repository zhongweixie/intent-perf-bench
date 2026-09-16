#include <cuda_runtime.h>
#include <cstdio>

int main() {
    void* ptr = nullptr;
    size_t size = 268435456; // 256 MB
    cudaError_t err = cudaMalloc(&ptr, size);
    
    printf("cudaMalloc(%zu bytes): ", size);
    if (err == cudaSuccess) {
        printf("SUCCESS\n");
        cudaFree(ptr);
    } else {
        printf("FAILED - %s\n", cudaGetErrorString(err));
    }
    
    // Check device properties
    int device;
    cudaGetDevice(&device);
    cudaDeviceProp prop;
    cudaGetDeviceProperties(&prop, device);
    printf("Device: %s\n", prop.name);
    printf("Total global memory: %.2f GB\n", prop.totalGlobalMem / 1024.0 / 1024.0 / 1024.0);
    printf("Free memory: ");
    size_t free_mem, total_mem;
    cudaMemGetInfo(&free_mem, &total_mem);
    printf("%.2f GB / %.2f GB\n", free_mem / 1024.0 / 1024.0 / 1024.0, total_mem / 1024.0 / 1024.0 / 1024.0);
    
    return 0;
}
