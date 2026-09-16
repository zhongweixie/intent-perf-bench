#include <iostream>
#include <cmath>
#include <chrono>
#include "include/cuda_utils.h"
#include "include/reduce.h"

void cpu_reduce(float *input, float &result, int n) {
    result = 0.0f;
    for (int i = 0; i < n; i++) {
        result += input[i];
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
        // Run kernel
        k_reduce<<<gridSize, blockSize, blockSize * sizeof(float)>>>(d_input, d_output, n);
        CUDA_CHECK(cudaGetLastError());
        CUDA_CHECK(cudaDeviceSynchronize());

        CUDA_CHECK(cudaMemcpy(h_output, d_output, gridSize * sizeof(float), cudaMemcpyDeviceToHost));

        // Sum up block results
        float gpu_result = 0.0f;
        for (int i = 0; i < gridSize; i++) {
            gpu_result += h_output[i];
        }

        // CPU reference
        float cpu_result;
        cpu_reduce(h_input, cpu_result, n);

        float diff = std::abs(gpu_result - cpu_result);
        float rel_error = diff / std::max(std::abs(cpu_result), 1e-6f);

        if (rel_error < 1e-4) {
            std::cout << "VERIFICATION PASSED" << std::endl;
            std::cout << "GPU result: " << gpu_result << std::endl;
            std::cout << "CPU result: " << cpu_result << std::endl;
            std::cout << "Relative error: " << rel_error << std::endl;
        } else {
            std::cout << "VERIFICATION FAILED" << std::endl;
            std::cout << "GPU result: " << gpu_result << std::endl;
            std::cout << "CPU result: " << cpu_result << std::endl;
            std::cout << "Relative error: " << rel_error << std::endl;
        }
    }

    if (benchmark_mode) {
        // Warmup
        for (int i = 0; i < 10; i++) {
            k_reduce<<<gridSize, blockSize, blockSize * sizeof(float)>>>(d_input, d_output, n);
        }
        CUDA_CHECK(cudaDeviceSynchronize());

        // Benchmark
        const int num_runs = 100;
        auto start = std::chrono::high_resolution_clock::now();
        for (int i = 0; i < num_runs; i++) {
            k_reduce<<<gridSize, blockSize, blockSize * sizeof(float)>>>(d_input, d_output, n);
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
