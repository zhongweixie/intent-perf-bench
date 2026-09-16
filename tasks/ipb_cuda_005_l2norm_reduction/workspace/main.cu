#include <iostream>
#include <cmath>
#include <chrono>
#include "include/cuda_utils.h"
#include "include/l2_norm.h"

void cpu_l2_norm(float *input, float &result, int n, bool square) {
    result = 0.0f;
    for (int i = 0; i < n; i++) {
        float val = square ? input[i] * input[i] : input[i];
        result += val;
    }
    if (!square) {
        result = std::sqrt(result);
    } else {
        result = std::sqrt(result);
    }
}

int main(int argc, char **argv) {
    bool verify_mode = false;
    bool benchmark_mode = false;

    for (int i = 1; i < argc; i++) {
        if (std::string(argv[i]) == "--verify") verify_mode = true;
        if (std::string(argv[i]) == "--benchmark") benchmark_mode = true;
    }

    const int n = 1 << 20;  // 1M elements
    const int blockSize = 256;
    const int gridSize = (n + blockSize - 1) / blockSize;

    float *h_input = new float[n];
    float *h_output = new float[gridSize];

    // Initialize with random values
    for (int i = 0; i < n; i++) {
        h_input[i] = static_cast<float>(rand()) / RAND_MAX;
    }

    float *d_input, *d_output;
    CUDA_CHECK(cudaMalloc(&d_input, n * sizeof(float)));
    CUDA_CHECK(cudaMalloc(&d_output, gridSize * sizeof(float)));
    CUDA_CHECK(cudaMemcpy(d_input, h_input, n * sizeof(float), cudaMemcpyHostToDevice));

    if (verify_mode) {
        // Run kernel with square=true (computes sum of squares)
        k_l2Norm<<<gridSize, blockSize, blockSize * sizeof(float)>>>(d_input, d_output, n, true);
        CUDA_CHECK(cudaGetLastError());
        CUDA_CHECK(cudaDeviceSynchronize());

        CUDA_CHECK(cudaMemcpy(h_output, d_output, gridSize * sizeof(float), cudaMemcpyDeviceToHost));

        // Sum up block results
        float gpu_result = 0.0f;
        for (int i = 0; i < gridSize; i++) {
            gpu_result += h_output[i];
        }
        gpu_result = std::sqrt(gpu_result);

        // CPU reference - also compute with square=true to match GPU
        float cpu_result;
        cpu_l2_norm(h_input, cpu_result, n, true);

        float diff = std::abs(gpu_result - cpu_result);
        if (diff < EPSILON) {
            std::cout << "VERIFICATION PASSED" << std::endl;
            std::cout << "GPU result: " << gpu_result << std::endl;
            std::cout << "CPU result: " << cpu_result << std::endl;
        } else {
            std::cout << "VERIFICATION FAILED" << std::endl;
            std::cout << "GPU result: " << gpu_result << std::endl;
            std::cout << "CPU result: " << cpu_result << std::endl;
            std::cout << "Difference: " << diff << std::endl;
        }
    }

    if (benchmark_mode) {
        // Warmup
        for (int i = 0; i < 10; i++) {
            k_l2Norm<<<gridSize, blockSize, blockSize * sizeof(float)>>>(d_input, d_output, n, true);
        }
        CUDA_CHECK(cudaDeviceSynchronize());

        // Benchmark
        const int num_runs = 100;
        auto start = std::chrono::high_resolution_clock::now();
        for (int i = 0; i < num_runs; i++) {
            k_l2Norm<<<gridSize, blockSize, blockSize * sizeof(float)>>>(d_input, d_output, n, true);
        }
        CUDA_CHECK(cudaDeviceSynchronize());
        auto end = std::chrono::high_resolution_clock::now();

        double elapsed = std::chrono::duration<double, std::milli>(end - start).count();
        std::cout << "Average time: " << elapsed / num_runs << " ms" << std::endl;
    }

    delete[] h_input;
    delete[] h_output;
    CUDA_CHECK(cudaFree(d_input));
    CUDA_CHECK(cudaFree(d_output));

    return 0;
}
