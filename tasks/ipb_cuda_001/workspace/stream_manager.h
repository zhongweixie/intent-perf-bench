/*
 * stream_manager.h -- manages temporary GPU memory for decode streams.
 */

#pragma once

#include <cuda_runtime.h>
#include <cstddef>

// Allocate temporary scratch buffer for a single decode stream
void* allocate_stream_scratch(size_t bytes, cudaStream_t stream);

// Free temporary scratch buffer
void free_stream_scratch(void* ptr, cudaStream_t stream);

// Batch allocate scratch buffers for K streams
void** allocate_batch_scratch(int K, size_t bytes_per_stream, cudaStream_t stream);

// Batch free scratch buffers
void free_batch_scratch(void** ptrs, int K, cudaStream_t stream);
