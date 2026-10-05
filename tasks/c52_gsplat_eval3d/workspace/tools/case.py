"""Thin fixed-input full-call feedback: original gsplat entry plus full VJP."""
from pathlib import Path
import argparse,hashlib,json,math,os,statistics,sys,time
TASK_ROOT=Path(os.environ.get('C52_TASK_ROOT',str(Path(__file__).resolve().parents[1])))
CONTRACT_ROOT=Path(os.environ.get('C52_CONTRACT_DIR',str(TASK_ROOT.parent/'.runtime/contract')))
sys.path.insert(0,str(TASK_ROOT))
import torch
import candidate
NAMES=['means','quats','scales','colors','opacities','backgrounds']
TOL=[.001,.0005,.001,.0001,.00015,.0016]
def bundle():return torch.load(CONTRACT_ROOT/'inputs.pt',map_location='cuda',weights_only=False)
def leaves(row):return {k:v.detach().clone().requires_grad_(True) for k,v in row['inputs'].items()}
def call(row,inputs):return candidate.run(inputs,row['meta'],row['weights'])
def hashes():
    root=TASK_ROOT;paths=[root/'candidate.py']+[p for p in (root/'gsplat').rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
def metric(a,b,atol,rtol):
    if a.shape!=b.shape:return {'passed':False,'shape':list(a.shape),'expected_shape':list(b.shape)}
    d=(a.detach()-b).abs();bad=d>(atol+rtol*b.abs());finite=bool(torch.isfinite(a).all())
    return {'passed':finite and not bool(bad.any()),'finite':finite,'failing_elements':int(bad.sum()),'elements':a.numel(),'max_abs_error':float(d.max()),'atol':atol,'rtol':rtol}
def check(data):
    expected=torch.load(CONTRACT_ROOT/'expected.pt',map_location='cuda',weights_only=False);records=[]
    for row,ref in zip(data,expected):
        inputs=leaves(row);outputs,grads=call(row,inputs)
        assert len(outputs)==2 and len(grads)==6
        tests={'colors':metric(outputs[0],ref['outputs'][0],.001,.003),'alpha':metric(outputs[1],ref['outputs'][1],.002,.01)}
        for n,g,e,t in zip(NAMES,grads,ref['grads'],TOL):tests['grad_'+n]=metric(g,e,t,0.)
        tests['background_structure']=metric(grads[-1],(row['weights'][0]*(1-outputs[1])).sum(dim=(-3,-2)),1e-6,1e-5)
        records.append({'shape':row['spec'],'metadata':row['info'],'checks':tests,'passed':all(v['passed'] for v in tests.values())})
    return {'mode':'check','passed':all(r['passed'] for r in records),'oracle':'fixed parent full tensors; known high-opacity Torch residual waived by user','no_excluded_elements':True,'records':records}
def bench(data,rounds):
    records=[]
    for row in data:
        if row['spec']['name'] not in ('ordinary','long_overlap','two_camera_features'):continue
        inputs=leaves(row)
        for _ in range(5):call(row,inputs)
        samples=[]
        for _ in range(rounds):
            torch.cuda.synchronize();start=time.perf_counter()
            for _ in range(20):call(row,inputs)
            torch.cuda.synchronize();samples.append((time.perf_counter()-start)*1000/20)
        records.append({'shape':row['spec'],'metadata':row['info'],'samples_ms':samples,'median_ms':statistics.median(samples)})
    return {'mode':'bench','passed':True,'records':records,'T_ms':math.exp(sum(math.log(r['median_ms']) for r in records)/len(records)),'boundary':'host synchronized run(inputs,meta,weights): full RGB/alpha plus six VJPs; includes target allocation, Python, preprocessing/state/sync; fixed inputs/meta/weights and oracle/compile excluded'}
def profile(data,trace_path):
    row=next(r for r in data if r['spec']['name']=='long_overlap');inputs=leaves(row);call(row,inputs);torch.cuda.synchronize()
    with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU,torch.profiler.ProfilerActivity.CUDA],record_shapes=True) as p:
        call(row,inputs);torch.cuda.synchronize()
    p.export_chrome_trace(str(trace_path))
    return {'mode':'profile','passed':True,'shape':row['spec'],'metadata':row['info'],'table':p.key_averages().table(sort_by='self_cuda_time_total',row_limit=25),'trace':str(trace_path)}
def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['check','bench','profile','submit']);p.add_argument('--output');p.add_argument('--rounds',type=int,default=3);a=p.parse_args()
    if a.mode=='submit':print('COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT');return
    if not a.output:raise ValueError('--output required')
    start=time.monotonic();data=bundle()
    result=check(data) if a.mode=='check' else bench(data,a.rounds) if a.mode=='bench' else profile(data,Path(a.output).with_name("profile.trace.json"))
    result.update(wall_s=time.monotonic()-start,source_hashes=hashes(),candidate_module=candidate.__file__,torch=torch.__version__,gpu=torch.cuda.get_device_name())
    Path(a.output).parent.mkdir(parents=True,exist_ok=True);Path(a.output).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='source_hashes'}));raise SystemExit(0 if result['passed'] else 2)
if __name__=='__main__':main()
