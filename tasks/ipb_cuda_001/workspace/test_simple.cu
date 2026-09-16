#include <stdio.h>
#include <cuda_runtime.h>

__global__ void hello() {
    printf("Hello from GPU thread %d\n", threadIdx.x);
}

int main() {
    printf("Testing basic CUDA functionality...\n");
    
    hello<<<1, 1>>>();
    cudaError_t err = cudaDeviceSynchronize();
    
    if (err != cudaSuccess) {
        printf("Kernel launch failed: %s\n", cudaGetErrorString(err));
        return 1;
    }
    
    printf("Success!\n");
    return 0;
}
