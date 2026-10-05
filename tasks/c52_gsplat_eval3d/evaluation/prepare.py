"""Freeze the seven C52 inputs and full parent outputs before an agent run."""
from pathlib import Path
import argparse,hashlib,json,os,sys,tempfile,zipfile

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'.runtime/contract')
    args=parser.parse_args()
    output=args.output.resolve()
    if output.exists() and any(output.iterdir()):
        raise RuntimeError('Refuse replacing an existing frozen contract; use a new output directory')
    output.mkdir(parents=True,exist_ok=True)
    oracle=Path(__file__).resolve().parent/'oracle.zip'
    definition=json.loads((oracle.parent/'contract.json').read_text(encoding='utf-8'))
    if hashlib.sha256(oracle.read_bytes()).hexdigest()!=definition['oracle_zip_sha256']:
        raise ValueError('Fixed parent oracle archive changed')
    source=Path(tempfile.mkdtemp(prefix='oracle-source-',dir=output.parent))
    with zipfile.ZipFile(oracle) as z:
        for name in z.namelist():
            path=Path(name)
            if path.is_absolute() or '..' in path.parts or not (name=='candidate.py' or name.startswith('gsplat/')):
                raise ValueError('Unsafe oracle archive member')
            target=source/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(name))
    os.environ['TORCH_EXTENSIONS_DIR']=str(output.parent/'oracle-extensions')
    sys.path.insert(0,str(source))
    import torch
    import candidate
    from fixtures import CHECK_SHAPES,BENCH_SHAPES,make,leaves
    if not torch.cuda.is_available():raise RuntimeError('C52 preparation requires a CUDA GPU')
    rows=[];expected=[]
    def cpu(value):
        if isinstance(value,torch.Tensor):return value.detach().cpu()
        if isinstance(value,dict):return {k:cpu(v) for k,v in value.items()}
        if isinstance(value,(tuple,list)):return type(value)(cpu(v) for v in value)
        return value
    for spec in CHECK_SHAPES+BENCH_SHAPES:
        values,meta,weights,info=make(spec)
        outputs,grads=candidate.run(leaves(values),meta,weights)
        rows.append(cpu(dict(spec=spec,inputs=values,meta=meta,weights=weights,info=info)))
        expected.append(cpu(dict(outputs=outputs,grads=grads)))
    torch.save(rows,output/'inputs.pt');torch.save(expected,output/'expected.pt')
    manifest=dict(case='C52',baseline_commit='3f1b4339c6a8d7898a47241b3fbe0bb86ba26507',conditions=[r['spec'] for r in rows],metadata=[r['info'] for r in rows],fixed_parent_equivalence=True,oracle_sha256=hashlib.sha256(oracle.read_bytes()).hexdigest(),files={name:hashlib.sha256((output/name).read_bytes()).hexdigest() for name in ('inputs.pt','expected.pt')},environment=dict(torch=torch.__version__,cuda=torch.version.cuda,gpu=torch.cuda.get_device_name()))
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(manifest))

if __name__=='__main__':main()
