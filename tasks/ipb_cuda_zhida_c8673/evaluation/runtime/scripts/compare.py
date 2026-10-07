import json
import sys
import torch

reference = torch.load(sys.argv[1], map_location='cpu', weights_only=True)
candidate = torch.load(sys.argv[2], map_location='cpu', weights_only=True)
errors = []
for name, ref in reference.items():
    if name not in candidate:
        errors.append(name + ': missing')
        continue
    got = candidate[name]
    dtype = torch.float16 if name.startswith('fp16') else torch.bfloat16
    for key in ('param','master','exp_avg','exp_avg_sq'):
        try:
            atol = torch.finfo(dtype).eps if key == 'param' else 1e-6
            torch.testing.assert_close(got[key], ref[key], rtol=1e-6, atol=atol, equal_nan=True)
        except Exception as exc:
            errors.append(name + '/' + key + ': ' + str(exc)[:180])
    for key in ('step','overflow'):
        if got[key] != ref[key]:
            errors.append(name + '/' + key + ': mismatch')
print(json.dumps({'correct': not errors, 'errors': errors}))
