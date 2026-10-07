Improve the complete GPU MoE block for the stated workload on RTX A6000. Diagnose the most useful correct performance change from the source and whole-pipeline measurements. Preserve behavior on all supported configurations. Leave your best tested correct source saved before the deadline. Only pipeline.py and routing.py are editable; the native and expert-kernel helpers are available to inspect and call. Your score is correct whole-pipeline latency, not a particular implementation. All workload and budget information is identical across conditions.


Background note:
On a skewed expert distribution, the routing IDs must be repacked into padded per-expert blocks before the matrix multiplications. The number of empty slots and how they map to programs could plausibly dominate realized efficiency; the source alone may not reveal the tradeoff between block size, packing, and occupancy. This is an unconfirmed explanation; measured end-to-end improvement is what matters.
