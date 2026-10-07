# Derived from vLLM 94923629729381d7f7c9efde72071a2441f7fd82.
import torch
import triton
import triton.language as tl
from expert_kernels import get_default_config, invoke_fused_moe_triton_kernel
from routing import grouped_topk
from native_ops import lib, check

@triton.jit
def activate(X,Y,N:tl.constexpr,TOTAL:tl.constexpr,B:tl.constexpr):
    i=tl.program_id(0)*B+tl.arange(0,B)
    row=i//N; col=i%N
    a=tl.load(X+row*(2*N)+col,i<TOTAL,0).to(tl.float32)
    b=tl.load(X+row*(2*N)+N+col,i<TOTAL,0).to(tl.float32)
    tl.store(Y+i,(a/(1+tl.exp(-a)))*b,i<TOTAL)

class Pipeline:
    def __init__(self,data):
        self.x,self.logits,self.w1,self.w2,self.groups,self.group_topk=data
        self.M,self.K=self.x.shape;self.E=self.w1.shape[0];self.N=self.w2.shape[-1];self.k=8
        M,E,N,K,k=self.M,self.E,self.N,self.K,self.k
        config=get_default_config(M,E,N,K,k,None)
        config['BLOCK_SIZE_M']=32
        self.config=config; block=config['BLOCK_SIZE_M']
        capacity=M*k+E*(block-1)
        if M*k<E:capacity=min(M*k*block,capacity)
        # Both variants use upstream default pad_sorted_ids=False capacity.
        self.sorted=torch.empty(capacity,device='cuda',dtype=torch.int32)
        self.experts=torch.empty(triton.cdiv(capacity,block),device='cuda',dtype=torch.int32)
        self.padded=torch.empty(1,device='cuda',dtype=torch.int32)
        self.cumsum=torch.empty(E+1,device='cuda',dtype=torch.int32)
        self.weights=torch.empty((M,k),device='cuda',dtype=torch.float32)
        self.ids=torch.empty((M,k),device='cuda',dtype=torch.int32)
        self.token_ids=torch.empty_like(self.ids);self.work=torch.empty_like(self.logits)
        self.h=torch.empty((M,k,2*N),device='cuda',dtype=torch.float16)
        self.act=torch.empty((M*k,N),device='cuda',dtype=torch.float16)
        self.parts=torch.empty((M,k,K),device='cuda',dtype=torch.float16)
        self.out=torch.empty_like(self.x)
        self.stage_fns=[self.routing,self.alignment,self.gemm1,self.activation,self.gemm2,self.reduce]

    def routing(self):
        self.weights,self.ids=grouped_topk(self.x,self.logits,self.k,True,self.groups,self.group_topk)

    def alignment(self):
        block=self.config['BLOCK_SIZE_M']
        if self.M*self.k*4<=self.E:
            # Upstream _prepare_expert_assignment's existing optimization.
            self.sorted_ids=None;self.expert_ids=self.ids.reshape(-1)
            self.padded.fill_(self.M*self.k*block)
        else:
            self.sorted_ids=self.sorted;self.expert_ids=self.experts
            check(lib.align(self.ids.data_ptr(),self.sorted.data_ptr(),self.experts.data_ptr(),self.padded.data_ptr(),self.cumsum.data_ptr(),self.E,block,self.M*self.k,self.sorted.numel(),self.k,torch.cuda.current_stream().cuda_stream))

    def invoke(self,a,b,c,k,weighted):
        invoke_fused_moe_triton_kernel(a,b,c,None,None,self.weights,self.sorted_ids,self.expert_ids,self.padded,weighted,k,self.config,tl.float16,False,False,False,False,False)
    def gemm1(self):self.invoke(self.x,self.w1,self.h,self.k,False)
    def activation(self):activate[(triton.cdiv(self.M*self.k*self.N,256),)](self.h,self.act,self.N,self.M*self.k*self.N,256)
    def gemm2(self):self.invoke(self.act,self.w2,self.parts,1,True)
    def reduce(self):
        torch.sum(self.parts,dim=1,out=self.out)
    def __call__(self):
        for f in self.stage_fns:f()
        return self.out

