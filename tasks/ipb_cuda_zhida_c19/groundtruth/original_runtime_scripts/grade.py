"""Fixed C26 loss/gradient checks and complete-call timing."""
import json, statistics, sys, time
from pathlib import Path

def main():
    repo, record, mode = sys.argv[1:4]
    sys.path.insert(0, repo)
    import torch
    from jsd_loss import LigerFusedLinearJSDFunction as Function
    torch.set_num_threads(1)
    records = {}
    def make(bt,h,v,seed,dtype,frozen=True,bias=False,teacher_pad=0,ignored=False):
        torch.manual_seed(seed)
        x=torch.randn(bt,h,device='cuda',dtype=dtype).requires_grad_(True)
        w=(torch.randn(v,h,device='cuda',dtype=dtype)/h**.5).requires_grad_(not frozen)
        tx=torch.randn(bt,h,device='cuda',dtype=dtype)
        tw=torch.randn(v+teacher_pad,h,device='cuda',dtype=dtype)/h**.5
        y=torch.randint(v,(bt,),device='cuda')
        if ignored:y[::3]=-100
        sb=torch.randn(v,device='cuda',dtype=dtype).requires_grad_(True) if bias else None
        tb=torch.randn(v+teacher_pad,device='cuda',dtype=dtype) if bias else None
        return x,w,tx,tw,y,sb,tb
    def call(tensors,hard=0.,beta=.5,temp=1.,compiled=False,chunk=4,parts=False,scale=1.):
        x,w,tx,tw,y,sb,tb=tensors
        x.grad=None; w.grad=None
        if sb is not None:sb.grad=None
        out=Function.apply(x,w,tx,tw,y,sb,tb,hard,1.,beta,-100,temp,compiled,chunk,parts)
        loss=out[0] if isinstance(out,tuple) else out
        (loss*scale).backward()
        return out
    def capture(name,tensors,out):
        x,w,tx,tw,y,sb,tb=tensors
        fields={'loss':out[0] if isinstance(out,tuple) else out,'input_grad':x.grad,
                'weight_grad':w.grad,'bias_grad':None if sb is None else sb.grad,
                'teacher_input_grad':tx.grad,'teacher_weight_grad':tw.grad}
        if isinstance(out,tuple):
            fields.update(soft=out[1],hard=out[2])
        records[name]={k:None if v is None else v.detach().cpu().clone() for k,v in fields.items()}
    for i in range(8):
        tensors=make(13,16,32,2600+i,torch.float32,frozen=i%2==0,bias=i>=4,teacher_pad=8 if i==7 else 0,ignored=i>=2)
        out=call(tensors,hard=.5 if i%3==1 else 0.,beta=[0.,.5,1.,.5][i%4],
                 temp=1.7 if i>=4 else 1.,parts=i%3==2,scale=.7 if i>=4 else 1.)
        capture('fp32_'+str(i),tensors,out)
    tensors=make(2048,1024,32768,20260928,torch.bfloat16)
    for _ in range(3):out=call(tensors,compiled=True,chunk=256)
    torch.cuda.synchronize()
    capture('bf16_target',tensors,out)
    torch.save(records,record)
    result={'correct':True,'errors':[],'records_written':record,'compiled':True}
    if mode!='oracle':
        samples=[]
        for _ in range(15 if mode=='interim' else 31):
            torch.cuda.synchronize()
            start=time.perf_counter_ns()
            call(tensors,compiled=True,chunk=256)
            torch.cuda.synchronize()
            samples.append((time.perf_counter_ns()-start)/1e6)
        result.update(latency_ms=statistics.median(samples),samples_ms=samples)
    print(json.dumps(result))

if __name__=='__main__':
    try: main()
    except Exception as exc:print(json.dumps({'correct':False,'errors':[type(exc).__name__+': '+str(exc)[:12000]]}))
