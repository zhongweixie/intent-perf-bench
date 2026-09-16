#include "transpose.h"
#include "cuda_helpers.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <string>
#include <math.h>

// Correctness test
void launch() {
    const int N = 512;  // Smaller size for correctness test
    const int size = N * N * sizeof(float);

    // Allocate host memory
    float* h_input = new float[N * N];
    float* h_output = new float[N * N];
    float* h_expected = new float[N * N];

    // Initialize input matrix with pattern
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            h_input[i * N + j] = i * N + j;
            h_expected[j * N + i] = i * N + j;  // Transpose
        }
    }

    // Allocate device memory
    float *d_input, *d_output;
    CUDA_CHECK(cudaMalloc(&d_input, size));
    CUDA_CHECK(cudaMalloc(&d_output, size));

    // Copy to device
    CUDA_CHECK(cudaMemcpy(d_input, h_input, size, cudaMemcpyHostToDevice));

    // Launch kernel
    dim3 blockDim(32, 32);
    dim3 gridDim((N + blockDim.x - 1) / blockDim.x,
                 (N + blockDim.y - 1) / blockDim.y);

    k_transpose<<<gridDim, blockDim>>>(d_input, d_output, N);
    CUDA_CHECK(cudaGetLastError());
    CUDA_CHECK(cudaDeviceSynchronize());

    // Copy result back
    CUDA_CHECK(cudaMemcpy(h_output, d_output, size, cudaMemcpyDeviceToHost));

    // Verify
    bool correct = true;
    for (int i = 0; i < N * N; i++) {
        if (fabs(h_output[i] - h_expected[i]) > 1e-5) {
            printf("Mismatch at index %d: got %f, expected %f\n",
                   i, h_output[i], h_expected[i]);
            correct = false;
            break;
        }
    }

    if (correct) {
        printf("PASS\n");
    } else {
        printf("FAIL\n");
    }

    // Cleanup
    CUDA_CHECK(cudaFree(d_input));
    CUDA_CHECK(cudaFree(d_output));
    delete[] h_input;
    delete[] h_output;
    delete[] h_expected;
}

// Performance benchmark
void benchmark() {
    const int N = MATRIX_SIZE;
    const int size = N * N * sizeof(float);
    const int warmupIters = 3;
    const int timedIters = 100;

    // Allocate device memory
    float *d_input, *d_output;
    CUDA_CHECK(cudaMalloc(&d_input, size));
    CUDA_CHECK(cudaMalloc(&d_output, size));

    // Initialize with dummy data
    CUDA_CHECK(cudaMemset(d_input, 0, size));

    // Launch configuration
    dim3 blockDim(32, 32);
    dim3 gridDim((N + blockDim.x - 1) / blockDim.x,
                 (N + blockDim.y - 1) / blockDim.y);

    // Warmup
    for (int i = 0; i < warmupIters; i++) {
        k_transpose<<<gridDim, blockDim>>>(d_input, d_output, N);
    }
    CUDA_CHECK(cudaDeviceSynchronize());

    // Timed run
    cudaEvent_t start, stop;
    CUDA_CHECK(cudaEventCreate(&start));
    CUDA_CHECK(cudaEventCreate(&stop));

    CUDA_CHECK(cudaEventRecord(start));
    for (int i = 0; i < timedIters; i++) {
        k_transpose<<<gridDim, blockDim>>>(d_input, d_output, N);
    }
    CUDA_CHECK(cudaEventRecord(stop));
    CUDA_CHECK(cudaEventSynchronize(stop));

    float milliseconds = 0;
    CUDA_CHECK(cudaEventElapsedTime(&milliseconds, start, stop));
    float avgTime = milliseconds / timedIters;

    // Output JSON format
    printf("{\"time_ms\": %.2f, \"cycles\": %d, \"runs\": %d, \"executable\": \"transpose_test\"}\n",
           avgTime, (int)(avgTime + 0.5), timedIters);

    // Cleanup
    CUDA_CHECK(cudaEventDestroy(start));
    CUDA_CHECK(cudaEventDestroy(stop));
    CUDA_CHECK(cudaFree(d_input));
    CUDA_CHECK(cudaFree(d_output));
}

int main(int argc, char** argv) {
    if (argc > 1 && std::string(argv[1]) == "--perf") {
        benchmark();
    } else {
        launch();
    }
    return 0;
}
