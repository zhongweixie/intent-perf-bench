"""The unchanged seven registered C52 workload definitions and input recipe."""
import math
import torch
from gsplat.cuda._wrapper import fully_fused_projection_with_ut,isect_tiles,isect_offset_encode

NAMES=['means','quats','scales','colors','opacities','backgrounds']

CHECK_SHAPES=[
    dict(name='small_rgb',N=16,C=1,D=3,W=32,H=24,opacity=.10,cluster=False,seed=123),
    dict(name='camera_feature_tail',N=33,C=2,D=5,W=35,H=27,opacity=.06,cluster=False,seed=124),
    dict(name='long_tile',N=257,C=1,D=3,W=32,H=32,opacity=.015,cluster=True,seed=125),
    dict(name='saturated_alpha',N=16,C=1,D=3,W=32,H=24,opacity=1.,cluster=True,seed=126),
]

BENCH_SHAPES=[
    dict(name='ordinary',N=256,C=1,D=3,W=128,H=96,opacity=.12,cluster=False,seed=223),
    dict(name='long_overlap',N=2048,C=1,D=3,W=128,H=96,opacity=.006,cluster=True,seed=224),
    dict(name='two_camera_features',N=512,C=2,D=5,W=128,H=96,opacity=.06,cluster=False,seed=225),
]

def make(spec):
    torch.manual_seed(spec['seed'])
    N,C,D,W,H=[spec[k] for k in ['N','C','D','W','H']]
    means=torch.randn(N,3,device='cuda')
    means[:,:2]*=.05 if spec['cluster'] else .6
    means[:,2]=3+torch.linspace(0,.4,N,device='cuda')
    quats=torch.nn.functional.normalize(torch.randn(N,4,device='cuda'),dim=-1)
    scales=.12+.20*torch.rand(N,3,device='cuda')
    if spec['cluster']: scales*=1.7
    opacity=spec['opacity']*(.85+.15*torch.rand(N,device='cuda'))
    if spec['name']=='saturated_alpha': opacity=torch.ones(N,device='cuda')
    colors=torch.rand(C,N,D,device='cuda')
    backgrounds=torch.rand(C,D,device='cuda')
    viewmats=torch.eye(4,device='cuda')[None].repeat(C,1,1)
    if C>1: viewmats[1,0,3]=.04
    focal=max(W,H)*1.4
    Ks=torch.tensor([[focal,0.,W/2],[0.,focal,H/2],[0.,0.,1.]],device='cuda')[None].repeat(C,1,1)
    with torch.no_grad():
        radii,means2d,depths,*_=fully_fused_projection_with_ut(means,quats,scales,opacity,viewmats,Ks,W,H,camera_model='pinhole')
        _,ids,flatten=isect_tiles(means2d,radii,depths,16,math.ceil(W/16),math.ceil(H/16))
        offsets=isect_offset_encode(ids,C,math.ceil(W/16),math.ceil(H/16)).reshape(C,math.ceil(H/16),math.ceil(W/16))
    values=dict(means=means,quats=quats,scales=scales,colors=colors,opacities=opacity[None].repeat(C,1),backgrounds=backgrounds)
    meta=dict(viewmats=viewmats,Ks=Ks,image_width=W,image_height=H,tile_size=16,isect_offsets=offsets,flatten_ids=flatten)
    weights=(torch.randn(C,H,W,D,device='cuda'),torch.randn(C,H,W,1,device='cuda'))
    flat=offsets.flatten().to(torch.int64)
    ends=torch.cat([flat[1:],torch.tensor([flatten.numel()],device='cuda')])
    lengths=ends-flat
    info={'intersections':flatten.numel(),'tile_count':flat.numel(),'nonempty_tiles':int((lengths>0).sum()),'tile_depth_max':int(lengths.max()),'tile_depth_mean':float(lengths.float().mean())}
    if info['intersections']==0: raise RuntimeError('Invalid preparation fixture: no Gaussian/tile intersections')
    return values,meta,weights,info

def leaves(values): return {k:v.detach().clone().requires_grad_(True) for k,v in values.items()}

