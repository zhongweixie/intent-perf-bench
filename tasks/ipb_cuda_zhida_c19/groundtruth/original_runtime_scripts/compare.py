import json,sys,torch
ref=torch.load(sys.argv[1],map_location='cpu',weights_only=True)
got=torch.load(sys.argv[2],map_location='cpu',weights_only=True)
errors=[]
for name,fields in ref.items():
    if name not in got:
        errors.append(name+': missing');continue
    for key,value in fields.items():
        other=got[name].get(key)
        try:
            if value is None:
                assert other is None,'expected no gradient'
            else:
                assert other is not None,'missing output/gradient'
                assert torch.isfinite(other).all(),'nonfinite output'
                grad='grad' in key
                atol=(1e-9 if grad else 2e-4) if name.startswith('bf16') else 1e-6
                rtol=.03 if name.startswith('bf16') else 1e-4
                torch.testing.assert_close(other,value,rtol=rtol,atol=atol,equal_nan=False)
        except Exception as exc:errors.append(name+'/'+key+': '+str(exc)[:160])
print(json.dumps({'correct':not errors,'errors':errors}))
