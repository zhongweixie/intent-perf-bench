# L2 Norm Reduction: Shared Memory Bank Conflicts

Profiling shows significant bank conflicts in shared memory accesses during the reduction phase. Multiple threads are accessing the same bank simultaneously, causing serialization.

Pad the shared memory array or restructure access patterns to eliminate bank conflicts.
