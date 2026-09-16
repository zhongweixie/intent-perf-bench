#ifndef KMEANS_H
#define KMEANS_H

__global__ void k_assignClusters(float* pointsX_d, float* pointsY_d, 
                                float* centroidsX_d, float* centroidsY_d,
                                float* sumsX_d, float* sumsY_d, int* counts_d,
                                int* assignments_d, int numPoints, 
                                int numClusters);

__global__ void k_updateCentroids(float* centroidsX_d, float* centroidsY_d,
                                 float* sumsX_d, float* sumsY_d, int* counts_d,
                                 int numClusters);

#endif // KMEANS_H