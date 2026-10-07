"""Zero-API researcher check that the isolated C19 grader admits the known route optimization."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from remote_client import evaluate
from remote_controller import sources

files = sources()
old = "        self.weights,self.ids=grouped_topk(self.x,self.logits,self.k,True,self.groups,self.group_topk)"
new = """        if self.groups == 1 and self.group_topk == 1:
            check(lib.route(self.logits.data_ptr(), self.weights.data_ptr(),
                            self.ids.data_ptr(), self.token_ids.data_ptr(),
                            self.work.data_ptr(), self.M, self.E, self.k,
                            torch.cuda.current_stream().cuda_stream))
        else:
            self.weights,self.ids=grouped_topk(self.x,self.logits,self.k,True,self.groups,self.group_topk)"""
if files["pipeline.py"].count(old) != 1:
    raise RuntimeError("unexpected baseline")
files["pipeline.py"] = files["pipeline.py"].replace(old, new)
result = evaluate(files, "c19-route-reference", timeout=300, final=True)
print({key: value for key, value in result.items() if key != "samples_us"})
