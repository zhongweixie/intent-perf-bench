#!/bin/bash
# Shared GPU launcher for every code path that measures performance:
# calibration, agent evaluation and sanity checks all go through ipb_gpu_run,
# so the numbers being compared are always produced by identical commands.
#
# Reuses a long-lived `salloc --no-shell` allocation when one exists. A cold
# `srun` on this cluster queues ~3 min; `srun --overlap` into an existing
# allocation starts in ~11 s.

IPB_CUDA_BIN="${IPB_CUDA_BIN:-/home/hansirui_3rd/cuda-12/bin}"

# Newest RUNNING no-shell allocation owned by this user, if any.
#
# IPB_GPU_JOBID short-circuits the lookup. squeue on this cluster can take tens
# of seconds under scheduler load, and a failure here is silent: the caller
# just sees an empty id and cold-starts a fresh `srun -p debug` instead. With
# several measurements in flight that also trips QOSMaxJobsPerUserLimit, and
# the cancelled job surfaces as a measurement failure rather than as the queue
# problem it actually is. Resolving the id once per batch avoids both.
ipb_gpu_jobid() {
    if [ -n "$IPB_GPU_JOBID" ]; then
        echo "$IPB_GPU_JOBID"
        return
    fi
    squeue -u "$USER" -h -t RUNNING -o "%i %j" 2>/dev/null \
        | awk '$2 == "no-shell" { print $1 }' | sort -n | tail -1
}

ipb_gpu_run() {
    local jid
    jid="$(ipb_gpu_jobid)"
    export PATH="$IPB_CUDA_BIN:$PATH"
    if [ -n "$jid" ]; then
        srun --jobid="$jid" --overlap --gres=gpu:1 "$@"
    else
        srun -p debug --qos=llm_debug --gres=gpu:1 -t 10 "$@"
    fi
}
