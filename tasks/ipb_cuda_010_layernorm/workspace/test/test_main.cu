#include "layernorm.h"
#include "cuda_helpers.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <assert.h>

const float TOLERANCE = 1e-4f;

// CPU reference implementation
void layernorm_cpu(float* out, float* mean, float* rstd,
                   const float* inp, const float* weight, const float* bias,
                   int N, int C) {
    const float eps = 1e-5f;
    for (int i = 0; i < N; i++) {
        const float* x = inp + i * C;
        float* o = out + i * C;

        // Compute mean
        float m = 0.0f;
        for (int j = 0; j < C; j++) {
            m += x[j];
        }
        m = m / C;
        if (mean) mean[i] = m;

        // Compute variance
        float v = 0.0f;
        for (int j = 0; j < C; j++) {
            float diff = x[j] - m;
            v += diff * diff;
        }
        v = v / C;
        float s = 1.0f / sqrtf(v + eps);
        if (rstd) rstd[i] = s;

        // Normalize and scale
        for (int j = 0; j < C; j++) {
            float n = s * (x[j] - m);
            o[j] = n * weight[j] + bias[j];
        }
    }
}

void launch() {
    const int N = 1024;
    const int C = 768;
    const int size = N * C;

    // Allocate host memory
    float* h_inp = (float*)malloc(size * sizeof(float));
    float* h_weight = (float*)malloc(C * sizeof(float));
    float* h_bias = (float*)malloc(C * sizeof(float));
    float* h_out = (float*)malloc(size * sizeof(float));
    float* h_out_ref = (float*)malloc(size * sizeof(float));
    float* h_mean = (float*)malloc(N * sizeof(float));
    float* h_rstd = (float*)malloc(N * sizeof(float));

    // Initialize data
    for (int i = 0; i < size; i++) {
        h_inp[i] = (float)rand() / RAND_MAX * 2.0f - 1.0f;
    }
    for (int i = 0; i < C; i++) {
        h_weight[i] = (float)rand() / RAND_MAX * 0.5f + 0.5f;
        h_bias[i] = (float)rand() / RAND_MAX * 0.2f - 0.1f;
    }

    // Compute CPU reference
    layernorm_cpu(h_out_ref, h_mean, h_rstd, h_inp, h_weight, h_bias, N, C);

    // Allocate device memory
    float *d_inp, *d_weight, *d_bias, *d_out, *d_mean, *d_rstd;
    CUDA_CHECK(cudaMalloc(&d_inp, size * sizeof(float)));
    CUDA_CHECK(cudaMalloc(&d_weight, C * sizeof(float)));
    CUDA_CHECK(cudaMalloc(&d_bias, C * sizeof(float)));
    CUDA_CHECK(cudaMalloc(&d_out, size * sizeof(float)));
    CUDA_CHECK(cudaMalloc(&d_mean, N * sizeof(float)));
    CUDA_CHECK(cudaMalloc(&d_rstd, N * sizeof(float)));

    // Copy to device
    CUDA_CHECK(cudaMemcpy(d_inp, h_inp, size * sizeof(float), cudaMemcpyHostToDevice));
    CUDA_CHECK(cudaMemcpy(d_weight, h_weight, C * sizeof(float), cudaMemcpyHostToDevice));
    CUDA_CHECK(cudaMemcpy(d_bias, h_bias, C * sizeof(float), cudaMemcpyHostToDevice));

    // Run kernel
    layernorm_forward(d_out, d_mean, d_rstd, d_inp, d_weight, d_bias, N, C);
    CUDA_CHECK(cudaDeviceSynchronize());

    // Copy back
    CUDA_CHECK(cudaMemcpy(h_out, d_out, size * sizeof(float), cudaMemcpyDeviceToHost));

    // Verify results
    int errors = 0;
    for (int i = 0; i < size; i++) {
        float diff = fabsf(h_out[i] - h_out_ref[i]);
        float max_val = fmaxf(fabsf(h_out[i]), fabsf(h_out_ref[i]));
        if (diff > TOLERANCE * max_val && diff > TOLERANCE) {
            errors++;
            if (errors < 5) {
                printf("Mismatch at %d: got %.6f, expected %.6f\n",
                       i, h_out[i], h_out_ref[i]);
            }
        }
    }

    if (errors > 0) {
        printf("FAILED: %d mismatches found\n", errors);
        exit(1);
    }

    printf("PASSED: All values match within tolerance\n");

    // Cleanup
    free(h_inp);
    free(h_weight);
    free(h_bias);
    free(h_out);
    free(h_out_ref);
    free(h_mean);
    free(h_rstd);
    CUDA_CHECK(cudaFree(d_inp));
    CUDA_CHECK(cudaFree(d_weight));
    CUDA_CHECK(cudaFree(d_bias));
    CUDA_CHECK(cudaFree(d_out));
    CUDA_CHECK(cudaFree(d_mean));
    CUDA_CHECK(cudaFree(d_rstd));
}

void benchmark() {
    const int N = 8192;
    const int C = 768;
    const int size = N * C;
    const int warmup = 5;
    const int iters = 100;

    // Allocate and initialize
    float *h_inp = (float*)malloc(size * sizeof(float));
    float *h_weight = (float*)malloc(C * sizeof(float));
    float *h_bias = (float*)malloc(C * sizeof(float));
    for (int i = 0; i < size; i++) h_inp[i] = (float)rand() / RAND_MAX;
    for (int i = 0; i < C; i++) {
        h_weight[i] = 1.0f;
        h_bias[i] = 0.0f;
    }

    float *d_inp, *d_weight, *d_bias, *d_out, *d_mean, *d_rstd;
    CUDA_CHECK(cudaMalloc(&d_inp, size * sizeof(float)));
    CUDA_CHECK(cudaMalloc(&d_weight, C * sizeof(float)));
    CUDA_CHECK(cudaMalloc(&d_bias, C * sizeof(float)));
    CUDA_CHECK(cudaMalloc(&d_out, size * sizeof(float)));
    CUDA_CHECK(cudaMalloc(&d_mean, N * sizeof(float)));
    CUDA_CHECK(cudaMalloc(&d_rstd, N * sizeof(float)));

    CUDA_CHECK(cudaMemcpy(d_inp, h_inp, size * sizeof(float), cudaMemcpyHostToDevice));
    CUDA_CHECK(cudaMemcpy(d_weight, h_weight, C * sizeof(float), cudaMemcpyHostToDevice));
    CUDA_CHECK(cudaMemcpy(d_bias, h_bias, C * sizeof(float), cudaMemcpyHostToDevice));

    // Warmup
    for (int i = 0; i < warmup; i++) {
        layernorm_forward(d_out, d_mean, d_rstd, d_inp, d_weight, d_bias, N, C);
    }
    CUDA_CHECK(cudaDeviceSynchronize());

    // Benchmark
    cudaEvent_t start, stop;
    CUDA_CHECK(cudaEventCreate(&start));
    CUDA_CHECK(cudaEventCreate(&stop));

    CUDA_CHECK(cudaEventRecord(start));
    for (int i = 0; i < iters; i++) {
        layernorm_forward(d_out, d_mean, d_rstd, d_inp, d_weight, d_bias, N, C);
    }
    CUDA_CHECK(cudaEventRecord(stop));
    CUDA_CHECK(cudaEventSynchronize(stop));

    float elapsed_ms;
    CUDA_CHECK(cudaEventElapsedTime(&elapsed_ms, start, stop));
    float avg_ms = elapsed_ms / iters;

    printf("{\"benchmark\": \"layernorm\", \"N\": %d, \"C\": %d, \"time_ms\": %.6f, \"iters\": %d}\n",
           N, C, avg_ms, iters);

    // Cleanup
    free(h_inp);
    free(h_weight);
    free(h_bias);
    CUDA_CHECK(cudaFree(d_inp));
    CUDA_CHECK(cudaFree(d_weight));
    CUDA_CHECK(cudaFree(d_bias));
    CUDA_CHECK(cudaFree(d_out));
    CUDA_CHECK(cudaFree(d_mean));
    CUDA_CHECK(cudaFree(d_rstd));
    CUDA_CHECK(cudaEventDestroy(start));
    CUDA_CHECK(cudaEventDestroy(stop));
}

int main(int argc, char** argv) {
    if (argc > 1 && strcmp(argv[1], "--benchmark") == 0) {
        benchmark();
    } else {
        launch();
    }
    return 0;
}
