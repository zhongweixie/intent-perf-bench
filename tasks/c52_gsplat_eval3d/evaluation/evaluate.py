"""Run C52 full correctness and synchronized timing on a workspace or final ZIP."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,tempfile,zipfile

ROOT=Path(__file__).resolve().parents[1]

def resolve_candidate(path):
    path=path.resolve()
    if path.is_dir():return path
    if not path.is_file() or path.suffix!='.zip':raise ValueError('--candidate must be a workspace or final-source.zip')
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    parent=ROOT/'.runtime/candidates';parent.mkdir(parents=True,exist_ok=True)
    target=Path(tempfile.mkdtemp(prefix=digest[:16]+'-',dir=parent))
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            rel=Path(name)
            if rel.is_absolute() or '..' in rel.parts or not (name=='candidate.py' or name.startswith('gsplat/')):
                raise ValueError('Unsafe candidate archive member')
            dest=target/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(name))
    return target

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,default=ROOT/'workspace')
    parser.add_argument('--contract',type=Path,default=ROOT/'.runtime/contract')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--rounds',type=int,default=3)
    args=parser.parse_args()
    if args.rounds<1:raise ValueError('--rounds must be positive')
    contract=args.contract.resolve()
    manifest=json.loads((contract/'manifest.json').read_text(encoding='utf-8'))
    if manifest['case']!='C52' or len(manifest['conditions'])!=7:raise ValueError('Wrong contract')
    for name,digest in manifest['files'].items():
        if name not in ('inputs.pt','expected.pt'):raise ValueError('Unexpected contract file')
        if hashlib.sha256((contract/name).read_bytes()).hexdigest()!=digest:raise ValueError('Frozen contract changed')
    workspace=resolve_candidate(args.candidate)
    if not (workspace/'candidate.py').is_file() or not (workspace/'gsplat').is_dir():raise ValueError('Incomplete workspace')
    output=args.output.resolve();output.parent.mkdir(parents=True,exist_ok=True)
    cache_key=hashlib.sha256(str(workspace).encode()).hexdigest()[:16]
    env=os.environ.copy();env.update(C52_TASK_ROOT=str(workspace),C52_CONTRACT_DIR=str(contract),TORCH_EXTENSIONS_DIR=str(ROOT/'.runtime/extensions'/cache_key))
    tool=ROOT/'workspace/tools/case.py'
    result=dict(case='C52',candidate=str(args.candidate),contract_manifest=manifest,correctness=None,performance=None)
    for mode in ('check','bench'):
        file=output.with_name(output.stem+'.'+mode+'.json')
        command=[sys.executable,str(tool),mode,'--output',str(file)]
        if mode=='bench':command.extend(['--rounds',str(args.rounds)])
        process=subprocess.run(command,env=env,cwd=workspace)
        if file.exists():
            data=json.loads(file.read_text(encoding='utf-8'))
            result['correctness' if mode=='check' else 'performance']=data
        else:data={'passed':False}
        if process.returncode or not data.get('passed'):
            result['passed']=False;output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');raise SystemExit(process.returncode or 2)
        if mode=='check' and (len(data['records'])!=7 or sum(len(r['checks']) for r in data['records'])!=63):
            raise ValueError('Incomplete correctness coverage')
    result.update(passed=True,T_ms=result['performance']['T_ms'])
    output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':True,'T_ms':result['T_ms'],'output':str(output)}))

if __name__=='__main__':main()
