"""Prepare portable dependency locations; no model API requests or experiments."""
import argparse, json, os, shutil, subprocess, sys
from pathlib import Path

TASK=Path(__file__).resolve().parents[1]
RUNTIME=TASK/'evaluation/runtime'

def main():
    p=argparse.ArgumentParser();p.add_argument('--install-extra',action='store_true');a=p.parse_args()
    cfg=json.loads((TASK/'task.json').read_text())
    if sys.platform!='linux':raise RuntimeError('CUDA graders require Linux and Landlock ABI >=3')
    public=RUNTIME/'public'
    if not public.exists():public.symlink_to(TASK/'workspace/repo',target_is_directory=True)
    if cfg['case']=='C19':
        dst=RUNTIME/'source_base/native/kernels.so';dst.parent.mkdir(parents=True,exist_ok=True)
        src=RUNTIME/'vendor/native'
        if not dst.exists():
            nvcc=os.environ.get('IPB_NVCC') or shutil.which('nvcc') or '/usr/local/cuda/bin/nvcc'
            subprocess.run([nvcc,'-O3','-std=c++17','-shared','-Xcompiler','-fPIC','-arch=sm_86',
                            '-I',str(src),str(src/'topk.cu'),str(src/'align.cu'),'-o',str(dst)],check=True)
    if cfg['case']=='C8673':
        source=RUNTIME/'source_base'
        for relative,target in [('deepspeed/accelerator','../accelerator'),('deepspeed/ops/op_builder','../../op_builder'),('deepspeed/ops/csrc','../../csrc')]:
            link=source/relative
            if not link.exists():link.symlink_to(target,target_is_directory=True)
        site=RUNTIME/'extra_site';site.mkdir(exist_ok=True)
        if a.install_extra:
            subprocess.run([os.environ.get('IPB_PYTHON',sys.executable),'-m','pip','install','--upgrade','--target',str(site),
                            '-r',str(TASK/'requirements-extra.txt')],check=True)
    (RUNTIME/'runtime_env.json').write_text(json.dumps({
        'IPB_PYTHON':os.environ.get('IPB_PYTHON',sys.executable),
        'IPB_GPU':os.environ.get('IPB_GPU','0'),
        'IPB_BASE_PREFIX':os.environ.get('IPB_BASE_PREFIX',sys.base_prefix)
    },indent=2),encoding='utf8')
    print(json.dumps({'task_id':cfg['task_id'],'prepared':True}))

if __name__=='__main__':main()
