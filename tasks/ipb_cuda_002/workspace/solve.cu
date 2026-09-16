/* GPU ICP correspondence.  The tree is supplied by the caller; in particular,
 * do not fall back to an O(N*M) scan here. */
#include "solve.h"
#include "kdtree.h"

#include <cuda_runtime.h>
#include <cfloat>

namespace {
constexpr int BLOCK = 256;
constexpr int NACC  = 17; // sum p, sum q, sum pq, error, count

/* These are deliberately persistent.  Allocating them once (during warmup)
 * avoids putting a cudaMalloc/cudaFree synchronization point in every ICP
 * iteration. */
static double *g_acc = nullptr;

__device__ __forceinline__ float bbox_distance2(const KDNode& n,
                                                 float x, float y, float z) {
    float dx = x < n.bbox_min[0] ? n.bbox_min[0] - x :
               (x > n.bbox_max[0] ? x - n.bbox_max[0] : 0.0f);
    float dy = y < n.bbox_min[1] ? n.bbox_min[1] - y :
               (y > n.bbox_max[1] ? y - n.bbox_max[1] : 0.0f);
    float dz = z < n.bbox_min[2] ? n.bbox_min[2] - z :
               (z > n.bbox_max[2] ? z - n.bbox_max[2] : 0.0f);
    return dx * dx + dy * dy + dz * dz;
}

/* Search the supplied balanced KD tree.  The explicit stack is bounded by
 * tree depth (about 20 for the benchmark), not by its number of nodes. */
__global__ void correspondence_kernel(const float* __restrict__ src,
                                      const float* __restrict__ tgt,
                                      const KDNode* __restrict__ nodes,
                                      int N, float max_d2,
                                      double* __restrict__ acc,
                                      int* __restrict__ count_out) {
    __shared__ double partial[NACC][BLOCK];

    const int tid = threadIdx.x;
    const int i = blockIdx.x * blockDim.x + tid;
    double v[NACC];
#pragma unroll
    for (int k = 0; k < NACC; ++k) v[k] = 0.0;

    if (i < N) {
        const float px = src[3 * i];
        const float py = src[3 * i + 1];
        const float pz = src[3 * i + 2];

        /* Starting at max_d2 is intentional: points outside the acceptance
         * radius need not search the entire tree merely to be rejected. */
        float best = max_d2;
        int best_j = -1;
        int stack[32];
        int sp = 0;
        stack[sp++] = 0;
        while (sp) {
            const KDNode node = nodes[stack[--sp]];
            if (bbox_distance2(node, px, py, pz) >= best) continue;

            const int j = node.point_idx;
            const float dx = px - tgt[3 * j];
            const float dy = py - tgt[3 * j + 1];
            const float dz = pz - tgt[3 * j + 2];
            const float d2 = dx * dx + dy * dy + dz * dz;
            if (d2 < best) {
                best = d2;
                best_j = j;
            }

            /* Visit the split side containing p first.  It normally gives a
             * close candidate immediately, allowing its sibling to be
             * discarded when popped. */
            const int l = node.left;
            const int r = node.right;
            const float pivot = node.axis == 0 ? tgt[3 * j] :
                                (node.axis == 1 ? tgt[3 * j + 1] : tgt[3 * j + 2]);
            const float coord = node.axis == 0 ? px : (node.axis == 1 ? py : pz);
            const int near_child = coord < pivot ? l : r;
            const int far_child  = coord < pivot ? r : l;
            /* Push far first because this is a LIFO stack. */
            if (far_child >= 0 && bbox_distance2(nodes[far_child], px, py, pz) < best)
                stack[sp++] = far_child;
            if (near_child >= 0 && bbox_distance2(nodes[near_child], px, py, pz) < best)
                stack[sp++] = near_child;
        }

        if (best_j >= 0) {
            const double qx = (double)tgt[3 * best_j];
            const double qy = (double)tgt[3 * best_j + 1];
            const double qz = (double)tgt[3 * best_j + 2];
            const double x = (double)px, y = (double)py, z = (double)pz;
            v[0] = x;  v[1] = y;  v[2] = z;
            v[3] = qx; v[4] = qy; v[5] = qz;
            v[6] = x*qx; v[7] = x*qy; v[8] = x*qz;
            v[9] = y*qx; v[10] = y*qy; v[11] = y*qz;
            v[12] = z*qx; v[13] = z*qy; v[14] = z*qz;
            v[15] = (double)best;
            v[16] = 1.0;
        }
    }

#pragma unroll
    for (int k = 0; k < NACC; ++k) partial[k][tid] = v[k];
    __syncthreads();
    for (int stride = BLOCK / 2; stride; stride >>= 1) {
        if (tid < stride) {
#pragma unroll
            for (int k = 0; k < NACC; ++k)
                partial[k][tid] += partial[k][tid + stride];
        }
        __syncthreads();
    }
    if (tid == 0) {
#pragma unroll
        for (int k = 0; k < NACC; ++k) atomicAdd(&acc[k], partial[k][0]);
        atomicAdd(count_out, (int)partial[16][0]);
    }
}

/* Convert raw moments to centered covariance entirely on the device.  This
 * removes the D2H copy and cudaStreamSynchronize that formerly split the
 * operation into two kernels. */
__global__ void finalize_kernel(const double* __restrict__ a,
                                float* __restrict__ H,
                                float* __restrict__ err) {
    const int t = threadIdx.x;
    const double n = a[16];
    if (t < 9) {
        if (n == 0.0) {
            H[t] = 0.0f;
        } else {
            double raw = a[6 + t];
            int row = t / 3, col = t % 3;
            H[t] = (float)(raw - a[row] * a[3 + col] / n);
        }
    }
    if (t == 9) *err = (float)a[15];
}

inline void ensure_scratch() {
    if (!g_acc) cudaMalloc(&g_acc, NACC * sizeof(double));
}
} // namespace

void icp_correspondence(const float* src, const float* tgt, int N, int M,
                        float d_max, const void* kd_nodes, int n_nodes,
                        float* H_out, float* err_out, int* count_out,
                        cudaStream_t stream) {
    (void)M;
    ensure_scratch();
    cudaMemsetAsync(g_acc, 0, NACC * sizeof(double), stream);
    cudaMemsetAsync(count_out, 0, sizeof(int), stream);

    if (N <= 0 || n_nodes <= 0) {
        cudaMemsetAsync(H_out, 0, 9 * sizeof(float), stream);
        cudaMemsetAsync(err_out, 0, sizeof(float), stream);
        return;
    }
    int grid = (N + BLOCK - 1) / BLOCK;
    correspondence_kernel<<<grid, BLOCK, 0, stream>>>(
        src, tgt, static_cast<const KDNode*>(kd_nodes), N, d_max * d_max,
        g_acc, count_out);
    finalize_kernel<<<1, 32, 0, stream>>>(g_acc, H_out, err_out);
}
