#include "kmeans.h"
#include <cuda_runtime.h>
#include <float.h>

__global__ void k_assignClusters(float* pointsX_d, float* pointsY_d, 
                                float* __restrict__ centroidsX_d, float* __restrict__ centroidsY_d,
                                float* sumsX_d, float* sumsY_d, int* counts_d,
                                int* assignments_d, int numPoints, 
                                int numClusters) {
    extern __shared__ float s_centroidTile[];
    const int TILE_SIZE = warpSize;  // Optimal for shared memory capacity
    float* s_tileX = s_centroidTile;
    float* s_tileY = s_centroidTile + TILE_SIZE;

    int tid = threadIdx.x;
    int bid = blockIdx.x;
    int gid = bid * blockDim.x + tid;
    int numTiles = (numClusters + TILE_SIZE - 1) / TILE_SIZE;

    // Grid-stride loop for points
    for(int pid = gid; pid < numPoints; pid += gridDim.x * blockDim.x) {
        float px = pointsX_d[pid];
        float py = pointsY_d[pid];
        float minDist = FLT_MAX;
        int bestCluster = -1;

        // Process centroids in tiles
        for(int tile = 0; tile < numTiles; ++tile) {
            int tileStart = tile * TILE_SIZE;
            int tileEnd = min(tileStart + TILE_SIZE, numClusters);

            // Cooperative loading of centroid tile
            for(int i = tid; i < TILE_SIZE; i += blockDim.x) {
                int c = tileStart + i;
                if(c < numClusters) {
                    s_tileX[i] = centroidsX_d[c];
                    s_tileY[i] = centroidsY_d[c];
                }
            }
            __syncthreads();

            // Process current tile
            for(int i = 0; i < tileEnd - tileStart; ++i) {
                float dx = px - s_tileX[i];
                float dy = py - s_tileY[i];
                float dist = dx*dx + dy*dy;
                
                if(dist < minDist) {
                    minDist = dist;
                    bestCluster = tileStart + i;
                }
            }
            __syncthreads();
        }

        // Update global memory after processing all tiles
        if(bestCluster != -1) {
            assignments_d[pid] = bestCluster;
            atomicAdd(&counts_d[bestCluster], 1);
            atomicAdd(&sumsX_d[bestCluster], px);
            atomicAdd(&sumsY_d[bestCluster], py);
        }
    }
}

__global__ void k_updateCentroids(float* centroidsX_d, float* centroidsY_d,
                                 float* sumsX_d, float* sumsY_d, int* counts_d,
                                 int numClusters) {
    int c = blockIdx.x * blockDim.x + threadIdx.x;
    if(c < numClusters) {
        int count = counts_d[c];
        if(count > 0) {
            centroidsX_d[c] = __fdividef(sumsX_d[c], count);
            centroidsY_d[c] = __fdividef(sumsY_d[c], count);
        }
    }
}