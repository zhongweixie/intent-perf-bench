# Private C19 correctness and whole-pipeline CUDA Graph timing.
import json, math, os, random, statistics, sys
from pathlib import Path
import torch
import triton
from pipeline import Pipeline

def inputs(case,seed):
    M,E,K,N,mode,G,GT=case
    gen=torch.Generator(device='cuda').manual_seed(seed)
    x=torch.randn(M,K,generator=gen,device='cuda',dtype=torch.float16)
    logits=torch.randn(M,E,generator=gen,device='cuda',dtype=torch.float32)
    if mode=='skewed':logits[:,:16]+=4
    w1=torch.randn(E,2*N,K,generator=gen,device='cuda',dtype=torch.float16)/math.sqrt(K)
    w2=torch.randn(E,K,N,generator=gen,device='cuda',dtype=torch.float16)/math.sqrt(N)
    return x,logits,w1,w2,G,GT

def reference(data):
    # Independent eager reference: route mathematically, then one ordinary matmul per expert.
    x,logits,w1,w2,G,GT=data;M,K=x.shape;E,_,_=w1.shape;N=w2.shape[-1]
    scores=logits.softmax(-1)
    gi=scores.view(M,G,E//G).max(-1).values.topk(GT,dim=-1).indices
    mask=torch.zeros(M,G,device='cuda',dtype=torch.bool).scatter_(1,gi,True)
    masked=scores.masked_fill(~mask[:,:,None].expand(M,G,E//G).reshape(M,E),-float('inf'))
    weights,ids=masked.topk(8,dim=-1);weights/=weights.sum(-1,keepdim=True)
    parts=torch.empty(M,8,K,device='cuda',dtype=torch.float16)
    for e in range(E):
        rows,slots=torch.where(ids==e)
        if rows.numel()==0:continue
        h=(x[rows].float()@w1[e].float().T).half()
        act=(torch.nn.functional.silu(h[:,:N].float())*h[:,N:].float()).half()
        out=act.float()@w2[e].float().T
        parts[rows,slots]=(out*weights[rows,slots,None]).half()
    return parts.float().sum(1),ids,weights

def correctness(p,ref):
    p();torch.cuda.synchronize()
    expected,ids,weights=ref
    delta=(p.out.float()-expected)
    rms=(delta.square().mean()/expected.square().mean().clamp_min(1e-20)).sqrt().item()
    maxerr=delta.abs().max().item()
    route_ok=torch.equal(p.ids.sort(-1).values.long(),ids.sort(-1).values)
    # Fixed FP16 tolerance chosen before measurements, including summation-order rounding.
    ok=route_ok and torch.isfinite(p.out).all().item() and rms<0.002 and maxerr<0.005
    return {'ok':bool(ok),'relative_rms':rms,'max_abs':maxerr,'route_set_equal':route_ok,'padded_slots':int(p.padded.item()),'block_m':p.config['BLOCK_SIZE_M']}

def capture(fn):
    for _ in range(5):fn()
    torch.cuda.synchronize()
    g=torch.cuda.CUDAGraph()
    with torch.cuda.graph(g):fn()
    for _ in range(20):g.replay()
    torch.cuda.synchronize()
    return g

def measure(g,n):
    start=torch.cuda.Event(enable_timing=True);end=torch.cuda.Event(enable_timing=True)
    start.record()
    for _ in range(n):g.replay()
    end.record();end.synchronize()
    return start.elapsed_time(end)*1000/n


def main():
    mode = sys.argv[3]
    torch.set_num_threads(1)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.cuda.set_per_process_memory_fraction(0.08)
    cases = [
        (128,128,512,256,'skewed',1,1),
        (48,128,512,256,'uniform',1,1),
        (48,128,512,256,'uniform',4,2),
    ]
    checks=[]
    target=None
    for index,case in enumerate(cases):
        data=inputs(case,314159+index)
        expected=reference(data)
        pipe=Pipeline(data)
        result=correctness(pipe,expected)
        checks.append({'case':index, **result})
        if not result['ok']:
            print(json.dumps({'correct':False,'checks':checks,'errors':['correctness failed for case '+str(index)]}))
            return
        if index==0:target=pipe
    graph=capture(target)
    samples=[measure(graph,50) for _ in range(5 if mode=='interim' else 9)]
    print(json.dumps({'correct':True,'checks':checks,'latency_us':statistics.median(samples),
                      'samples_us':samples,'errors':[]}))

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print(json.dumps({'correct':False,'errors':[type(exc).__name__+': '+str(exc)[:12000]]}))
