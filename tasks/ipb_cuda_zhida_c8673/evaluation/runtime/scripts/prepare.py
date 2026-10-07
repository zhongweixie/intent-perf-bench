"""One-time clean base export from the already preflighted DeepSpeed checkout."""
import json
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = Path('/home/cthong/ipb-candidates/candidate8673-preflight')
BASE = 'bc778b8'
MAPPING = {
    'fused_optimizer.py': 'deepspeed/runtime/fp16/fused_optimizer.py',
    'fused_adam.py': 'deepspeed/ops/adam/fused_adam.py',
    'utils.py': 'deepspeed/runtime/utils.py',
    'multi_tensor_adam.cu': 'csrc/adam/multi_tensor_adam.cu',
    'fused_adam_frontend.cpp': 'csrc/adam/fused_adam_frontend.cpp',
    'multi_tensor_apply.cuh': 'csrc/adam/multi_tensor_apply.cuh',
}

def main():
    template = ROOT/'source_base'
    if template.exists():
        print('PREPARED', template)
        return
    template.mkdir()
    proc = subprocess.Popen(['git','-C',str(UPSTREAM),'archive',BASE], stdout=subprocess.PIPE)
    with tarfile.open(fileobj=proc.stdout, mode='r|') as archive:
        archive.extractall(template, filter='data')
    if proc.wait():
        raise RuntimeError('base archive failed')
    shutil.copy2(UPSTREAM/'preflight_artifacts'/'bench.py', template/'_pilot_bench.py')
    shutil.copy2(ROOT/'scripts'/'grade.py',template/'_pilot_grade.py')
    public = ROOT/'public'
    public.mkdir()
    for alias, path in MAPPING.items():
        shutil.copy2(template/path, public/alias)
    (public/'CONTRACT.md').write_text(
        'Task: optimize the full non-ZeRO FP16/BF16 FusedAdam wrapper step while preserving Adam/AdamW, '
        'loss scaling, clipping, overflow behavior and optimizer state. Edit only the listed source files. '
        'The public benchmark uses 64,000,000 FP16 elements, AdamW, clip_grad=0.5, static loss scale 128, '
        '20 warmups and 30 timed iterations on one RTX A6000. The benchmark tool reports absolute step latency '
        'and checks reference state. Source aliases map to:\n' +
        ''.join(f'{name}: {path}\n' for name,path in MAPPING.items()),encoding='utf-8')
    (ROOT/'private'/'mapping.json').write_text(json.dumps(MAPPING,indent=2))
    print('PREPARED', template)

if __name__ == '__main__':
    main()
