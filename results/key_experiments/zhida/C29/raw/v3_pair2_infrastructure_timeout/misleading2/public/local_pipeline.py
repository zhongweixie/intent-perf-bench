"""Fixed local movement driver. Expert computation is a scalar stand-in."""
import torch

def local_forward(module, rows, counts, scores, token_indices, top_k):
    reordered, perm, _, n_rows = module.permute_by_local_expert(rows, counts)
    expert_rows = module.unpermute_by_local_expert(reordered * 1.125, perm, n_rows)
    return module.combine_from_routed(expert_rows, scores, token_indices, top_k,
                                     'post', 'weighted_sum', (1, scores.shape[0], rows.shape[1]))

def local_step(module, rows, counts, scores, token_indices, top_k, upstream):
    with torch.no_grad():
        local_forward(module, rows, counts, scores, token_indices, top_k)
    result = local_forward(module, rows, counts, scores, token_indices, top_k)
    gradients = torch.autograd.grad(result, (rows, scores), upstream)
    return result, gradients
