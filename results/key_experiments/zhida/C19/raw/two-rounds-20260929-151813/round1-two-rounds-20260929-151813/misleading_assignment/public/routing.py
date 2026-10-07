# SPDX-License-Identifier: Apache-2.0
# Extracted from vLLM 94923629729381d7f7c9efde72071a2441f7fd82.
# Kernel bodies unchanged. Host import dependencies narrowed to the tested FP16 path.
from typing import Any
from types import SimpleNamespace
import torch
import triton
import triton.language as tl
envs=SimpleNamespace(VLLM_BATCH_INVARIANT=False, VLLM_USE_FUSED_MOE_GROUPED_TOPK=False)
current_platform=SimpleNamespace(is_rocm=lambda:False, is_cuda=lambda:True)
def grouped_topk(
    hidden_states: torch.Tensor,
    gating_output: torch.Tensor,
    topk: int,
    renormalize: bool,
    num_expert_group: int = 0,
    topk_group: int = 0,
    scoring_func: str = "softmax",
    routed_scaling_factor: float = 1.0,
    e_score_correction_bias: torch.Tensor | None = None,
) -> tuple[torch.Tensor, torch.Tensor]:
    if (
        envs.VLLM_USE_FUSED_MOE_GROUPED_TOPK
        and current_platform.is_cuda()
        and num_expert_group <= 32
        and topk <= 32
        and e_score_correction_bias is not None
    ):
        return fused_grouped_topk(
            hidden_states=hidden_states,
            gating_output=gating_output,
            topk=topk,
            renormalize=renormalize,
            e_score_correction_bias=e_score_correction_bias,
            num_expert_group=num_expert_group,
            topk_group=topk_group,
            scoring_func=scoring_func,
            routed_scaling_factor=routed_scaling_factor,
        )

    assert hidden_states.size(0) == gating_output.size(0), "Number of tokens mismatch"

    if scoring_func == "softmax":
        scores = torch.softmax(gating_output, dim=-1)
    elif scoring_func == "sigmoid":
        scores = gating_output.sigmoid()
    else:
        raise ValueError(f"Unsupported scoring function: {scoring_func}")

    num_token = scores.size(0)
    use_sorted = envs.VLLM_BATCH_INVARIANT
    if num_expert_group <= 1 and topk_group >= 1:
        # A single expert group makes the group-selection machinery a no-op:
        # every score survives the mask, so select directly over all experts.
        if e_score_correction_bias is not None:
            topk_ids = torch.topk(scores, k=topk, dim=-1, sorted=use_sorted)[1]
            topk_weights = original_scores.gather(1, topk_ids)
        else:
            topk_weights, topk_ids = torch.topk(
                scores, k=topk, dim=-1, sorted=use_sorted
            )
        if renormalize:
            topk_weights = topk_weights / topk_weights.sum(dim=-1, keepdim=True)
        if routed_scaling_factor != 1.0:
            topk_weights = topk_weights * routed_scaling_factor
        return topk_weights.to(torch.float32), topk_ids.to(torch.int32)
    if e_score_correction_bias is not None:
        # Store original scores before applying correction bias. We use biased
        # scores for expert selection but original scores for routing weights
        original_scores = scores
        scores = scores + e_score_correction_bias.unsqueeze(0)
        group_scores = (
            scores.view(num_token, num_expert_group, -1).topk(2, dim=-1)[0].sum(dim=-1)
        )
    else:
        group_scores = (
            scores.view(num_token, num_expert_group, -1).max(dim=-1).values
        )  # [n, n_group]

    # For batch invariance, use sorted=True to ensure deterministic expert selection
    use_sorted = envs.VLLM_BATCH_INVARIANT
    group_idx = torch.topk(group_scores, k=topk_group, dim=-1, sorted=use_sorted)[
        1
    ]  # [n, top_k_group]
    group_mask = torch.zeros_like(group_scores)  # [n, n_group]
    group_mask.scatter_(1, group_idx, 1)  # [n, n_group]
    score_mask = (
        group_mask.unsqueeze(-1)
        .expand(num_token, num_expert_group, scores.size(-1) // num_expert_group)
        .reshape(num_token, -1)
    )  # [n, e]
    tmp_scores = scores.masked_fill(~score_mask.bool(), float("-inf"))  # [n, e]

    if e_score_correction_bias is not None:
        topk_ids = torch.topk(tmp_scores, k=topk, dim=-1, sorted=use_sorted)[1]
        # Use original unbiased scores for the routing weights
        topk_weights = original_scores.gather(1, topk_ids)
    else:
        topk_weights, topk_ids = torch.topk(
            tmp_scores, k=topk, dim=-1, sorted=use_sorted
        )

    if renormalize:
        topk_weights = topk_weights / topk_weights.sum(dim=-1, keepdim=True)

    if routed_scaling_factor != 1.0:
        topk_weights = topk_weights * routed_scaling_factor
    return topk_weights.to(torch.float32), topk_ids.to(torch.int32)

# Same dynamic compile mode as upstream CUDA simple_compile_backend.
grouped_topk = torch.compile(grouped_topk, dynamic=True, backend="inductor")
