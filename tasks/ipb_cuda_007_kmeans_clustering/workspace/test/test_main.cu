#undef NDEBUG
#include <algorithm>
#include <assert.h>
#include <cuda_runtime.h>
#include <float.h>
#include <stdio.h>
#include <string>
#include <vector>
#include <nvtx3/nvToolsExt.h>
#include "kmeans.h"
#include "cuda_helpers.h"

const float TOLERANCE = 1e-5f;

struct TestCase2D {
    int numPoints;
    int numClusters;
    std::vector<float> pointsX;
    std::vector<float> pointsY;
    std::vector<float> centroidsX;
    std::vector<float> centroidsY;
    std::vector<float> expectedSumsX;
    std::vector<float> expectedSumsY;
    std::vector<int> expectedCounts;
    std::vector<int> expectedAssignments;
};

std::vector<TestCase2D> testCases = {
    // Test Case 0: Basic clustering
    {4, 2,
     {1, 2, 5, 6}, {1, 2, 5, 6},
     {1.5, 5.5}, {1.5, 5.5},
     {3, 11}, {3, 11},
     {2, 2}, {0, 0, 1, 1}},

    // Test Case 1: Single cluster
    {3, 1,
     {1, 2, 3}, {1, 2, 3},
     {2}, {2},
     {6}, {6},
     {3}, {0, 0, 0}},

    // Test Case 2: Edge case with equidistant points
    {5, 2,
     {0, 100, 50, 25, 75}, {0, 100, 50, 25, 75},
     {25, 75}, {25, 75},
     {75, 175}, {75, 175},
     {3, 2}, {0, 1, 0, 0, 1}},
};

void launch() {
    // Initialize CUDA runtime
    cudaFree(0);
    cudaDeviceProp prop;
    CUDA_CHECK(cudaGetDeviceProperties(&prop, 0));
    int numSMs = prop.multiProcessorCount;
    int targetBlocksPerSM = 4;
    int deviceWarpSize = prop.warpSize;
    
    // Create a CUDA stream for asynchronous operations
    cudaStream_t stream;
    CUDA_CHECK(cudaStreamCreate(&stream));

    for(const auto& tc : testCases) {
        // Host data
        std::vector<float> pointsX_h = tc.pointsX;
        std::vector<float> pointsY_h = tc.pointsY;
        std::vector<float> centroidsX_h = tc.centroidsX;
        std::vector<float> centroidsY_h = tc.centroidsY;
        std::vector<float> sumsX_h(tc.numClusters, 0);
        std::vector<float> sumsY_h(tc.numClusters, 0);
        std::vector<int> counts_h(tc.numClusters, 0);
        std::vector<int> assignments_h(tc.numPoints, -1);

        // Device pointers
        float *pointsX_d, *pointsY_d, *centroidsX_d, *centroidsY_d;
        float *sumsX_d, *sumsY_d;
        int *counts_d, *assignments_d;

        // Allocate device memory asynchronously
        CUDA_CHECK(cudaMallocAsync(&pointsX_d, tc.numPoints * sizeof(float), stream));
        CUDA_CHECK(cudaMallocAsync(&pointsY_d, tc.numPoints * sizeof(float), stream));
        CUDA_CHECK(cudaMallocAsync(&centroidsX_d, tc.numClusters * sizeof(float), stream));
        CUDA_CHECK(cudaMallocAsync(&centroidsY_d, tc.numClusters * sizeof(float), stream));
        CUDA_CHECK(cudaMallocAsync(&sumsX_d, tc.numClusters * sizeof(float), stream));
        CUDA_CHECK(cudaMallocAsync(&sumsY_d, tc.numClusters * sizeof(float), stream));
        CUDA_CHECK(cudaMallocAsync(&counts_d, tc.numClusters * sizeof(int), stream));
        CUDA_CHECK(cudaMallocAsync(&assignments_d, tc.numPoints * sizeof(int), stream));

        // Copy data to device asynchronously
        CUDA_CHECK(cudaMemcpyAsync(pointsX_d, pointsX_h.data(), tc.numPoints * sizeof(float), 
                                  cudaMemcpyHostToDevice, stream));
        CUDA_CHECK(cudaMemcpyAsync(pointsY_d, pointsY_h.data(), tc.numPoints * sizeof(float), 
                                  cudaMemcpyHostToDevice, stream));
        CUDA_CHECK(cudaMemcpyAsync(centroidsX_d, centroidsX_h.data(), tc.numClusters * sizeof(float), 
                                  cudaMemcpyHostToDevice, stream));
        CUDA_CHECK(cudaMemcpyAsync(centroidsY_d, centroidsY_h.data(), tc.numClusters * sizeof(float), 
                                  cudaMemcpyHostToDevice, stream));
        CUDA_CHECK(cudaMemsetAsync(sumsX_d, 0, tc.numClusters * sizeof(float), stream));
        CUDA_CHECK(cudaMemsetAsync(sumsY_d, 0, tc.numClusters * sizeof(float), stream));
        CUDA_CHECK(cudaMemsetAsync(counts_d, 0, tc.numClusters * sizeof(int), stream));

        // Phase 1: Assign clusters with SM-aware grid sizing
        int assignBlockSize = 256;
        int assignGridSize = (tc.numPoints + assignBlockSize - 1) / assignBlockSize;
        assignGridSize = std::min(prop.maxGridSize[0], std::max(assignGridSize, numSMs * targetBlocksPerSM));
        size_t sharedMem = 2 * deviceWarpSize * sizeof(float);
        
        // Set up kernel parameters for assignClusters kernel
        // Create local copies of the integer parameters to avoid const issues
        int numPoints = tc.numPoints;
        int numClusters = tc.numClusters;
        
        void* assignArgs[] = {
            &pointsX_d, &pointsY_d, &centroidsX_d, &centroidsY_d,
            &sumsX_d, &sumsY_d, &counts_d, &assignments_d,
            &numPoints, &numClusters
        };
        
        dim3 assignGrid(assignGridSize);
        dim3 assignBlock(assignBlockSize);
        
        // Launch kernel using cudaLaunchKernel
        CUDA_CHECK(cudaLaunchKernel(
            (void*)k_assignClusters,
            assignGrid, assignBlock,
            assignArgs, sharedMem, stream
        ));
        
        // Phase 2: Update centroids with cluster-aware grid sizing
        int updateBlockSize = 256;
        int updateGridSize = (tc.numClusters + updateBlockSize - 1) / updateBlockSize;
        updateGridSize = std::max(updateGridSize, std::min(numSMs, tc.numClusters));
        
        // Set up kernel parameters for updateCentroids kernel
        void* updateArgs[] = {
            &centroidsX_d, &centroidsY_d, &sumsX_d, &sumsY_d, &counts_d, &numClusters
        };
        
        dim3 updateGrid(updateGridSize);
        dim3 updateBlock(updateBlockSize);
        
        // Launch kernel using cudaLaunchKernel
        CUDA_CHECK(cudaLaunchKernel(
            (void*)k_updateCentroids,
            updateGrid, updateBlock,
            updateArgs, 0, stream
        ));
        
        // Copy results back to host asynchronously
        CUDA_CHECK(cudaMemcpyAsync(sumsX_h.data(), sumsX_d, tc.numClusters * sizeof(float), 
                                  cudaMemcpyDeviceToHost, stream));
        CUDA_CHECK(cudaMemcpyAsync(sumsY_h.data(), sumsY_d, tc.numClusters * sizeof(float), 
                                  cudaMemcpyDeviceToHost, stream));
        CUDA_CHECK(cudaMemcpyAsync(counts_h.data(), counts_d, tc.numClusters * sizeof(int), 
                                  cudaMemcpyDeviceToHost, stream));
        CUDA_CHECK(cudaMemcpyAsync(assignments_h.data(), assignments_d, tc.numPoints * sizeof(int), 
                                  cudaMemcpyDeviceToHost, stream));
        
        // Synchronize to ensure all operations are complete before verification
        CUDA_CHECK(cudaStreamSynchronize(stream));

        // Verify results
        for(int i = 0; i < tc.numClusters; i++) {
            assert(fabs(sumsX_h[i] - tc.expectedSumsX[i]) < TOLERANCE);
            assert(fabs(sumsY_h[i] - tc.expectedSumsY[i]) < TOLERANCE);
            assert(counts_h[i] == tc.expectedCounts[i]);
        }
        for(int i = 0; i < tc.numPoints; i++) {
            assert(assignments_h[i] == tc.expectedAssignments[i]);
        }

        // Cleanup using asynchronous free
        CUDA_CHECK(cudaFreeAsync(pointsX_d, stream));
        CUDA_CHECK(cudaFreeAsync(pointsY_d, stream));
        CUDA_CHECK(cudaFreeAsync(centroidsX_d, stream));
        CUDA_CHECK(cudaFreeAsync(centroidsY_d, stream));
        CUDA_CHECK(cudaFreeAsync(sumsX_d, stream));
        CUDA_CHECK(cudaFreeAsync(sumsY_d, stream));
        CUDA_CHECK(cudaFreeAsync(counts_d, stream));
        CUDA_CHECK(cudaFreeAsync(assignments_d, stream));
    }

    // Ensure all asynchronous operations are complete before destroying the stream
    CUDA_CHECK(cudaStreamSynchronize(stream));
    CUDA_CHECK(cudaStreamDestroy(stream));

    // Print PASS for IPB verification
    printf("PASS\n");
}

void benchmark() {
    const int numPoints = 4000000;
    const int numClusters = 256;
    const int warmupIters = 3;
    const int timedIters = 100;

    cudaDeviceProp prop;
    CUDA_CHECK(cudaGetDeviceProperties(&prop, 0));
    int numSMs = prop.multiProcessorCount;
    int targetBlocksPerSM = 4;
    int deviceWarpSize = prop.warpSize;

    cudaStream_t stream;
    CUDA_CHECK(cudaStreamCreate(&stream));

    std::vector<float> pointsX_h(numPoints);
    std::vector<float> pointsY_h(numPoints);
    std::vector<float> centroidsX_h(numClusters);
    std::vector<float> centroidsY_h(numClusters);

    for (int i = 0; i < numPoints; i++) {
        pointsX_h[i] = static_cast<float>(i % 1000) + 0.5f;
        pointsY_h[i] = static_cast<float>((i * 7) % 1000) + 0.3f;
    }
    for (int i = 0; i < numClusters; i++) {
        centroidsX_h[i] = static_cast<float>(i * 1000 / numClusters) + 0.1f;
        centroidsY_h[i] = static_cast<float>(i * 1000 / numClusters) + 0.2f;
    }

    float *pointsX_d, *pointsY_d, *centroidsX_d, *centroidsY_d;
    float *sumsX_d, *sumsY_d;
    int *counts_d, *assignments_d;

    CUDA_CHECK(cudaMalloc(&pointsX_d, numPoints * sizeof(float)));
    CUDA_CHECK(cudaMalloc(&pointsY_d, numPoints * sizeof(float)));
    CUDA_CHECK(cudaMalloc(&centroidsX_d, numClusters * sizeof(float)));
    CUDA_CHECK(cudaMalloc(&centroidsY_d, numClusters * sizeof(float)));
    CUDA_CHECK(cudaMalloc(&sumsX_d, numClusters * sizeof(float)));
    CUDA_CHECK(cudaMalloc(&sumsY_d, numClusters * sizeof(float)));
    CUDA_CHECK(cudaMalloc(&counts_d, numClusters * sizeof(int)));
    CUDA_CHECK(cudaMalloc(&assignments_d, numPoints * sizeof(int)));

    CUDA_CHECK(cudaMemcpy(pointsX_d, pointsX_h.data(), numPoints * sizeof(float), cudaMemcpyHostToDevice));
    CUDA_CHECK(cudaMemcpy(pointsY_d, pointsY_h.data(), numPoints * sizeof(float), cudaMemcpyHostToDevice));

    int assignBlockSize = 256;
    int assignGridSize = (numPoints + assignBlockSize - 1) / assignBlockSize;
    assignGridSize = std::min(prop.maxGridSize[0], std::max(assignGridSize, numSMs * targetBlocksPerSM));
    size_t sharedMem = 2 * deviceWarpSize * sizeof(float);

    int updateBlockSize = 256;
    int updateGridSize = (numClusters + updateBlockSize - 1) / updateBlockSize;
    updateGridSize = std::max(updateGridSize, std::min(numSMs, numClusters));

    int np = numPoints;
    int nc = numClusters;

    auto runIteration = [&]() {
        CUDA_CHECK(cudaMemcpyAsync(centroidsX_d, centroidsX_h.data(), numClusters * sizeof(float), cudaMemcpyHostToDevice, stream));
        CUDA_CHECK(cudaMemcpyAsync(centroidsY_d, centroidsY_h.data(), numClusters * sizeof(float), cudaMemcpyHostToDevice, stream));
        CUDA_CHECK(cudaMemsetAsync(sumsX_d, 0, numClusters * sizeof(float), stream));
        CUDA_CHECK(cudaMemsetAsync(sumsY_d, 0, numClusters * sizeof(float), stream));
        CUDA_CHECK(cudaMemsetAsync(counts_d, 0, numClusters * sizeof(int), stream));

        void* assignArgs[] = {
            &pointsX_d, &pointsY_d, &centroidsX_d, &centroidsY_d,
            &sumsX_d, &sumsY_d, &counts_d, &assignments_d,
            &np, &nc
        };
        CUDA_CHECK(cudaLaunchKernel(
            (void*)k_assignClusters,
            dim3(assignGridSize), dim3(assignBlockSize),
            assignArgs, sharedMem, stream
        ));

        void* updateArgs[] = {
            &centroidsX_d, &centroidsY_d, &sumsX_d, &sumsY_d, &counts_d, &nc
        };
        CUDA_CHECK(cudaLaunchKernel(
            (void*)k_updateCentroids,
            dim3(updateGridSize), dim3(updateBlockSize),
            updateArgs, 0, stream
        ));
    };

    for (int i = 0; i < warmupIters; i++) {
        runIteration();
    }
    CUDA_CHECK(cudaStreamSynchronize(stream));

    // Timing for benchmark
    cudaEvent_t start, stop;
    CUDA_CHECK(cudaEventCreate(&start));
    CUDA_CHECK(cudaEventCreate(&stop));

    CUDA_CHECK(cudaEventRecord(start, stream));
    nvtxRangePushA("bench_region");
    for (int i = 0; i < timedIters; i++) {
        runIteration();
    }
    CUDA_CHECK(cudaStreamSynchronize(stream));
    nvtxRangePop();
    CUDA_CHECK(cudaEventRecord(stop, stream));
    CUDA_CHECK(cudaEventSynchronize(stop));

    float milliseconds = 0;
    CUDA_CHECK(cudaEventElapsedTime(&milliseconds, start, stop));

    // Output in JSON format for IPB benchmark parser
    printf("{\"time_ms\": %.2f, \"cycles\": %.0f, \"runs\": %d, \"executable\": \"kmeans_test\"}\n",
           milliseconds, milliseconds, timedIters);

    CUDA_CHECK(cudaEventDestroy(start));
    CUDA_CHECK(cudaEventDestroy(stop));

    CUDA_CHECK(cudaFree(pointsX_d));
    CUDA_CHECK(cudaFree(pointsY_d));
    CUDA_CHECK(cudaFree(centroidsX_d));
    CUDA_CHECK(cudaFree(centroidsY_d));
    CUDA_CHECK(cudaFree(sumsX_d));
    CUDA_CHECK(cudaFree(sumsY_d));
    CUDA_CHECK(cudaFree(counts_d));
    CUDA_CHECK(cudaFree(assignments_d));

    CUDA_CHECK(cudaStreamDestroy(stream));
}

int main(int argc, char** argv) {
    if (argc > 1 && std::string(argv[1]) == "--perf") {
        benchmark();
    } else {
        launch();
    }
}