"""Complete world-space eval3d RGB/alpha VJP entry. Editable."""
def run(inputs,meta,weights):
    import torch
    from gsplat.cuda._wrapper import rasterize_to_pixels_eval3d,RollingShutterType
    outputs=rasterize_to_pixels_eval3d(**inputs,**meta,camera_model='pinhole',rolling_shutter=RollingShutterType.GLOBAL,use_hit_distance=False)
    names=['means','quats','scales','colors','opacities','backgrounds']
    gradients=torch.autograd.grad(outputs,tuple(inputs[n] for n in names),grad_outputs=weights)
    return outputs,gradients
