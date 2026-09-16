#undef NDEBUG
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <algorithm>
#include <random>
#include <cuda.h>
#include <cuda_runtime.h>
#include <device_launch_parameters.h>
#include <nvtx3/nvToolsExt.h>
#include "convolution.h"

#define CUDA_CHECK(call) {                                     \
    cudaError_t error = call;                                  \
    if (error != cudaSuccess) {                                \
        fprintf(stderr, "CUDA error at %s: %d - %s \n",        \
                __FILE__, __LINE__, cudaGetErrorString(error));\
        exit(EXIT_FAILURE);                                    \
    }                                                          \
}

void launch() {
    constexpr int MAX_ARRAY_ELEMENTS = 100000;
    constexpr int NUM_TESTS = 7;
    constexpr int DETERMINISTIC_RANDOM_SEED = 42;
    constexpr float ERROR_TOLERANCE = 1e-3f;
    cudaDeviceProp deviceProperties;
    int deviceIndex = 0;
    CUDA_CHECK(cudaSetDevice(deviceIndex));
    CUDA_CHECK(cudaGetDeviceProperties(&deviceProperties, deviceIndex));
    
    cudaStream_t stream;
    CUDA_CHECK(cudaStreamCreate(&stream));
    
    // Allocating host memory.
    float* coefficients_h = new float[FILTER_WIDTH];
    float* array_h = new float[MAX_ARRAY_ELEMENTS];
    float* testArray_h = new float[NUM_TESTS * MAX_ARRAY_ELEMENTS];
    int* testArraySize_h = new int[NUM_TESTS];
    
    // Allocating device memory.
    float* inputArray_d;
    float* outputArray_d;
    float* coefficients_d;
    CUDA_CHECK(cudaMallocAsync(&inputArray_d, sizeof(float) * MAX_ARRAY_ELEMENTS, stream));
    CUDA_CHECK(cudaMallocAsync(&outputArray_d, sizeof(float) * MAX_ARRAY_ELEMENTS, stream));
    CUDA_CHECK(cudaMallocAsync(&coefficients_d, sizeof(float) * FILTER_WIDTH, stream));
    
    // Initializing the coefficients based on the heights from a Gaussian curve.
    float sumOfCoefficients = 0.0f;
    for (int index = 0; index < FILTER_WIDTH; index++) {
        float coefficient = expf(-((index - FILTER_CENTER_INDEX) * (index - FILTER_CENTER_INDEX)) / SQUARED_STD_MULT_2);
        coefficients_h[index] = coefficient;
        sumOfCoefficients += coefficient;
    }
    CUDA_CHECK(cudaMemcpyAsync(coefficients_d, coefficients_h, sizeof(float) * FILTER_WIDTH, cudaMemcpyHostToDevice, stream));
    int testIndex = 0;
    // Preparing the test data.
    // Test 1:
    {
        int arraySize = 10;
        testArraySize_h[testIndex] = arraySize;
        std::initializer_list<float> testData = { 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0 };
        std::copy(testData.begin(), testData.end(), &testArray_h[testIndex * MAX_ARRAY_ELEMENTS]);
        testIndex++;
    }
    // Test 2:
    {
        int arraySize = 5;
        testArraySize_h[testIndex] = arraySize;
        std::initializer_list<float> testData = { 3.0, 4.0, 5.0, 6.0, 7.0 };
        std::copy(testData.begin(), testData.end(), &testArray_h[testIndex * MAX_ARRAY_ELEMENTS]);
        testIndex++;
    }
    // Test 3:
    {
        int arraySize = 1000;
        testArraySize_h[testIndex] = arraySize;
        for (int i = 0; i < arraySize; i++) {
            testArray_h[testIndex * MAX_ARRAY_ELEMENTS + i] = sinf(i * 0.001f);
        }
        testIndex++;
    }
    // Test 4:
    {
        int arraySize = 1001;
        std::mt19937 generator(DETERMINISTIC_RANDOM_SEED);
        std::uniform_real_distribution<float> distribution(0.0f, 1.0f);
        testArraySize_h[testIndex] = arraySize;
        for (int i = 0; i < arraySize; i++) {
            testArray_h[testIndex * MAX_ARRAY_ELEMENTS + i] = distribution(generator);
        }
        testIndex++;
    }
    // Test 5:
    {
        int arraySize = 1002;
        testArraySize_h[testIndex] = arraySize;
        for (int i = 0; i < arraySize; i++) {
            testArray_h[testIndex * MAX_ARRAY_ELEMENTS + i] = 1.0f / (i + 1);
        }
        testIndex++;
    }
    // Test 6:
    {
        int arraySize = 1;
        testArraySize_h[testIndex] = arraySize;
        for (int i = 0; i < arraySize; i++) {
            testArray_h[testIndex * MAX_ARRAY_ELEMENTS + i] = 41.0f;
        }
        testIndex++;
    }
    // Test 7:
    {
        int arraySize = MAX_ARRAY_ELEMENTS;
        testArraySize_h[testIndex] = arraySize;
        for (int i = 0; i < arraySize; i++) {
            testArray_h[testIndex * MAX_ARRAY_ELEMENTS + i] = ((i % 2) ? 1.0f : -1.0f);
        }
        testIndex++;
    }
    
    // Iterating the tests.
    for (int test = 0; test < testIndex; test++) {
        int arraySize = testArraySize_h[test];
        for (int i = 0; i < arraySize; i++) {
            array_h[i] = testArray_h[test * MAX_ARRAY_ELEMENTS + i];
        }
        CUDA_CHECK(cudaMemcpyAsync(inputArray_d, array_h, sizeof(float) * arraySize, cudaMemcpyHostToDevice, stream));
        void* args[] = { &coefficients_d, &sumOfCoefficients, &inputArray_d, &outputArray_d, &arraySize };
        
        int maxResidentBlocks = deviceProperties.maxBlocksPerMultiProcessor * deviceProperties.multiProcessorCount;
        // Using 1024 threads per block, for output tile size of 1024 elements and input tile size of 1024 + 200 elements.
        int blockSize = 1024;
        // Required shared memory size for convolution filter coefficients.
        size_t sharedMemForFilter = FILTER_WIDTH * sizeof(float);
        // Required shared memory size for the tiling, which includes the halo region of size (FILTER_WIDTH - 1) and the interior of size blockSize.
        size_t sharedMemForTile = (blockSize + (FILTER_WIDTH - 1)) * sizeof(float);
        size_t sharedMem = sharedMemForFilter + sharedMemForTile;
        
        int requiredNumberOfBlocks = (arraySize + blockSize - 1) / blockSize;
        // Limiting the grid size accordingly with the computational resources of the GPU.
        int gridSize = requiredNumberOfBlocks < maxResidentBlocks ? requiredNumberOfBlocks : maxResidentBlocks;
        // Grid: (gridSize, 1, 1)
        // Block: (blockSize, 1, 1)
        CUDA_CHECK(cudaLaunchKernel((void*)k_runConvolution, dim3(gridSize, 1, 1), dim3(blockSize, 1, 1), args, sharedMem, stream));
        CUDA_CHECK(cudaMemcpyAsync(array_h, outputArray_d, sizeof(float) * arraySize, cudaMemcpyDeviceToHost, stream));
        CUDA_CHECK(cudaStreamSynchronize(stream));
        for (int i = 0; i < arraySize; i++) {
            float expectedResult = 0.0f;
            for (int j = 0; j < FILTER_WIDTH; j++) {
                float coefficient = coefficients_h[j];
                int index = i - HALF_OF_FILTER_WIDTH + j;
                float element = (index >= 0 && index < arraySize) ? testArray_h[test * MAX_ARRAY_ELEMENTS + index] : 0.0f;
                expectedResult = fmaf(coefficient, element, expectedResult);
            }
            expectedResult /= sumOfCoefficients;
            assert(fabsf(expectedResult - array_h[i]) / fabs(expectedResult) < ERROR_TOLERANCE);
        }
    }
    
    // Releasing device memory.
    CUDA_CHECK(cudaFreeAsync(inputArray_d, stream));
    CUDA_CHECK(cudaFreeAsync(outputArray_d, stream));
    CUDA_CHECK(cudaFreeAsync(coefficients_d, stream));
    // Releasing host memory.
    delete [] coefficients_h;
    delete [] array_h;
    delete [] testArray_h;
    delete [] testArraySize_h;
    CUDA_CHECK(cudaStreamSynchronize(stream));
    CUDA_CHECK(cudaStreamDestroy(stream));
}

void benchmark() {
    constexpr int BENCH_ARRAY_SIZE = 2000000;
    constexpr int WARMUP_ITERS = 3;
    constexpr int TIMED_ITERS = 100;

    cudaDeviceProp deviceProperties;
    int deviceIndex = 0;
    CUDA_CHECK(cudaSetDevice(deviceIndex));
    CUDA_CHECK(cudaGetDeviceProperties(&deviceProperties, deviceIndex));

    cudaStream_t stream;
    CUDA_CHECK(cudaStreamCreate(&stream));

    float* coefficients_h = new float[FILTER_WIDTH];
    float* array_h = new float[BENCH_ARRAY_SIZE];

    float* inputArray_d;
    float* outputArray_d;
    float* coefficients_d;
    CUDA_CHECK(cudaMallocAsync(&inputArray_d, sizeof(float) * BENCH_ARRAY_SIZE, stream));
    CUDA_CHECK(cudaMallocAsync(&outputArray_d, sizeof(float) * BENCH_ARRAY_SIZE, stream));
    CUDA_CHECK(cudaMallocAsync(&coefficients_d, sizeof(float) * FILTER_WIDTH, stream));

    float sumOfCoefficients = 0.0f;
    for (int index = 0; index < FILTER_WIDTH; index++) {
        float coefficient = expf(-((index - FILTER_CENTER_INDEX) * (index - FILTER_CENTER_INDEX)) / SQUARED_STD_MULT_2);
        coefficients_h[index] = coefficient;
        sumOfCoefficients += coefficient;
    }
    CUDA_CHECK(cudaMemcpyAsync(coefficients_d, coefficients_h, sizeof(float) * FILTER_WIDTH, cudaMemcpyHostToDevice, stream));

    std::mt19937 generator(123);
    std::uniform_real_distribution<float> distribution(-1.0f, 1.0f);
    for (int i = 0; i < BENCH_ARRAY_SIZE; i++) {
        array_h[i] = distribution(generator);
    }
    CUDA_CHECK(cudaMemcpyAsync(inputArray_d, array_h, sizeof(float) * BENCH_ARRAY_SIZE, cudaMemcpyHostToDevice, stream));

    int arraySize = BENCH_ARRAY_SIZE;
    int blockSize = 1024;
    size_t sharedMemForFilter = FILTER_WIDTH * sizeof(float);
    size_t sharedMemForTile = (blockSize + (FILTER_WIDTH - 1)) * sizeof(float);
    size_t sharedMem = sharedMemForFilter + sharedMemForTile;
    int maxResidentBlocks = deviceProperties.maxBlocksPerMultiProcessor * deviceProperties.multiProcessorCount;
    int requiredNumberOfBlocks = (arraySize + blockSize - 1) / blockSize;
    int gridSize = requiredNumberOfBlocks < maxResidentBlocks ? requiredNumberOfBlocks : maxResidentBlocks;
    void* args[] = { &coefficients_d, &sumOfCoefficients, &inputArray_d, &outputArray_d, &arraySize };

    for (int i = 0; i < WARMUP_ITERS; i++) {
        CUDA_CHECK(cudaLaunchKernel((void*)k_runConvolution, dim3(gridSize, 1, 1), dim3(blockSize, 1, 1), args, sharedMem, stream));
    }
    CUDA_CHECK(cudaStreamSynchronize(stream));

    // Timing for benchmark
    cudaEvent_t start, stop;
    CUDA_CHECK(cudaEventCreate(&start));
    CUDA_CHECK(cudaEventCreate(&stop));

    CUDA_CHECK(cudaEventRecord(start, stream));
    nvtxRangePushA("bench_region");
    for (int i = 0; i < TIMED_ITERS; i++) {
        CUDA_CHECK(cudaLaunchKernel((void*)k_runConvolution, dim3(gridSize, 1, 1), dim3(blockSize, 1, 1), args, sharedMem, stream));
    }
    CUDA_CHECK(cudaStreamSynchronize(stream));
    nvtxRangePop();
    CUDA_CHECK(cudaEventRecord(stop, stream));
    CUDA_CHECK(cudaEventSynchronize(stop));

    float milliseconds = 0;
    CUDA_CHECK(cudaEventElapsedTime(&milliseconds, start, stop));

    // Output in JSON format for IPB benchmark parser
    printf("{\"time_ms\": %.2f, \"cycles\": %.0f, \"runs\": %d, \"executable\": \"conv1d_test\"}\n",
           milliseconds, milliseconds, TIMED_ITERS);

    CUDA_CHECK(cudaEventDestroy(start));
    CUDA_CHECK(cudaEventDestroy(stop));

    CUDA_CHECK(cudaFreeAsync(inputArray_d, stream));
    CUDA_CHECK(cudaFreeAsync(outputArray_d, stream));
    CUDA_CHECK(cudaFreeAsync(coefficients_d, stream));
    delete[] coefficients_h;
    delete[] array_h;
    CUDA_CHECK(cudaStreamSynchronize(stream));
    CUDA_CHECK(cudaStreamDestroy(stream));
}

int main(int argc, char** argv) {
    if (argc > 1 && strcmp(argv[1], "--perf") == 0) {
        benchmark();
    } else {
        launch();
    }
}
