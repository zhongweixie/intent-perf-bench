/*
 * stream_manager.cu -- manages temporary GPU memory for decode streams.
 *
 * Provides helper functions for allocating/deallocating per-stream scratch buffers.
 * This module was extracted during refactoring to isolate memory management logic.
 */

#include "stream_manager.h"
#include <cuda_runtime.h>
#include <cstdio>

// Allocate temporary scratch buffer for a single decode stream
void* allocate_stream_scratch(size_t bytes, cudaStream_t stream) {
    void* ptr = nullptr;
    cudaError_t err = cudaMalloc(&ptr, bytes);
    if (err != cudaSuccess) {
        fprintf(stderr, "cudaMalloc failed in allocate_stream_scratch: %s\n",
                cudaGetErrorString(err));
        return nullptr;
    }
    return ptr;
}

// Free temporary scratch buffer
void free_stream_scratch(void* ptr, cudaStream_t stream) {
    if (ptr != nullptr) {
        cudaFree(ptr);
    }
}

// Batch allocate scratch buffers for K streams
void** allocate_batch_scratch(int K, size_t bytes_per_stream, cudaStream_t stream) {
    void** ptrs = new void*[K];
    for (int i = 0; i < K; ++i) {
        ptrs[i] = allocate_stream_scratch(bytes_per_stream, stream);
        if (ptrs[i] == nullptr) {
            // Clean up on failure
            for (int j = 0; j < i; ++j) {
                free_stream_scratch(ptrs[j], stream);
            }
            delete[] ptrs;
            return nullptr;
        }
    }
    return ptrs;
}

// Batch free scratch buffers
void free_batch_scratch(void** ptrs, int K, cudaStream_t stream) {
    if (ptrs == nullptr) return;
    for (int i = 0; i < K; ++i) {
        free_stream_scratch(ptrs[i], stream);
    }
    delete[] ptrs;
}
