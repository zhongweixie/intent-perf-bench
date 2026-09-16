#include <stdio.h>
#include <cuda_runtime.h>

int main() {
    printf("Step 1: Attempting cudaFree(0) to initialize CUDA context...\n");
    cudaError_t err = cudaFree(0);
    printf("cudaFree(0) returned: %s\n", cudaGetErrorString(err));
    
    printf("\nStep 2: Checking device count...\n");
    int deviceCount = 0;
    err = cudaGetDeviceCount(&deviceCount);
    printf("cudaGetDeviceCount returned: %s, count = %d\n", cudaGetErrorString(err), deviceCount);
    
    if (err == cudaSuccess && deviceCount > 0) {
        printf("\nStep 3: Getting device properties...\n");
        cudaDeviceProp prop;
        err = cudaGetDeviceProperties(&prop, 0);
        if (err == cudaSuccess) {
            printf("Device 0: %s\n", prop.name);
            printf("Compute capability: %d.%d\n", prop.major, prop.minor);
        } else {
            printf("cudaGetDeviceProperties failed: %s\n", cudaGetErrorString(err));
        }
    }
    
    return 0;
}
