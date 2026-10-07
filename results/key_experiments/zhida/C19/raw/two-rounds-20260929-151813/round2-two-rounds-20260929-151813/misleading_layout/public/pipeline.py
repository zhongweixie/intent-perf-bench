# Derived from vLLM 94923629729381d7f7c9efde72071a2441f7fd82.
import torch
import triton
import triton.language as tl
from expert_kernels import get_default_config, invoke_fused_moe_triton_kernel
from routing import grouped_topk
from native_ops import lib, check

@triton.jit
def gemm1_act_kernel(
    a_ptr, b_ptr, c_ptr,
    sorted_token_ids_ptr, expert_ids_ptr, num_tokens_post_padded_ptr,
    N, K, EM, num_valid_tokens,
    stride_am, stride_ak,
    stride_be, stride_bk, stride_bn,
    stride_cm, stride_cn,
    top_k: tl.constexpr,
    BLOCK_SIZE_M: tl.constexpr, BLOCK_SIZE_N: tl.constexpr,
    BLOCK_SIZE_K: tl.constexpr, GROUP_SIZE_M: tl.constexpr,
):
    pid = tl.program_id(axis=0)
    num_pid_m = tl.cdiv(EM, BLOCK_SIZE_M)
    num_pid_n = tl.cdiv(N, BLOCK_SIZE_N)
    num_pid_in_group = GROUP_SIZE_M * num_pid_n
    group_id = pid // num_pid_in_group
    first_pid_m = group_id * GROUP_SIZE_M
    group_size_m = min(num_pid_m - first_pid_m, GROUP_SIZE_M)
    pid_m = first_pid_m + ((pid % num_pid_in_group) % group_size_m)
    pid_n = (pid % num_pid_in_group) // group_size_m

    offs = tl.arange(0, BLOCK_SIZE_M).to(tl.int64)
    num_tokens_post_padded = tl.load(num_tokens_post_padded_ptr)
    if pid_m * BLOCK_SIZE_M >= num_tokens_post_padded:
        return
    offs_token_id = pid_m * BLOCK_SIZE_M + offs
    offs_token = tl.load(sorted_token_ids_ptr + offs_token_id).to(tl.int64)
    token_mask = offs_token < num_valid_tokens

    off_experts = tl.load(expert_ids_ptr + pid_m).to(tl.int64)
    offs_cn = pid_n * BLOCK_SIZE_N + tl.arange(0, BLOCK_SIZE_N)
    c_ptrs = c_ptr + stride_cm * offs_token[:, None] + stride_cn * offs_cn[None, :]
    c_mask = token_mask[:, None] & (offs_cn[None, :] < N)
    if off_experts == -1:
        tl.store(c_ptrs, tl.zeros((BLOCK_SIZE_M, BLOCK_SIZE_N), dtype=tl.float16), mask=c_mask)
        return

    offs_bn = (pid_n * BLOCK_SIZE_N + tl.arange(0, BLOCK_SIZE_N).to(tl.int64)) % N
    offs_k = tl.arange(0, BLOCK_SIZE_K)
    a_ptrs = a_ptr + (offs_token[:, None] // top_k * stride_am + offs_k[None, :] * stride_ak)
    b_ptrs = b_ptr + off_experts * stride_be + (offs_k[:, None] * stride_bk + offs_bn[None, :] * stride_bn)
    b_ptrs_up = b_ptrs + N * stride_bn

    acc_gate = tl.zeros((BLOCK_SIZE_M, BLOCK_SIZE_N), dtype=tl.float32)
    acc_up = tl.zeros((BLOCK_SIZE_M, BLOCK_SIZE_N), dtype=tl.float32)
    for k in range(0, tl.cdiv(K, BLOCK_SIZE_K)):
        kmask = offs_k[:, None] < K - k * BLOCK_SIZE_K
        a = tl.load(a_ptrs, mask=token_mask[:, None] & (offs_k[None, :] < K - k * BLOCK_SIZE_K), other=0.0)
        bg = tl.load(b_ptrs, mask=kmask, other=0.0)
        bu = tl.load(b_ptrs_up, mask=kmask, other=0.0)
        acc_gate += tl.dot(a, bg)
        acc_up += tl.dot(a, bu)
        a_ptrs += BLOCK_SIZE_K * stride_ak
        b_ptrs += BLOCK_SIZE_K * stride_bk
        b_ptrs_up += BLOCK_SIZE_K * stride_bk

    res = (acc_gate / (1 + tl.exp(-acc_gate))) * acc_up
    tl.store(c_ptrs, res.to(tl.float16), mask=c_mask)

class Pipeline:
    def __init__(self,data):
        self.x,self.logits,self.w1,self.w2,self.groups,self.group_topk=data
        self.M,self.K=self.x.shape;self.E=self.w1.shape[0];self.N=self.w2.shape[-1];self.k=8
        M,E,N,K,k=self.M,self.E,self.N,self.K,self.k
        config=get_default_config(M,E,N,K,k,None)
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
        self.act=torch.empty((M*k,N),device='cuda',dtype=torch.float16)
        self.parts=torch.empty((M,k,K),device='cuda',dtype=torch.float16)
        self.out=torch.empty_like(self.x)
        self.stage_fns=[self.routing,self.alignment,self.gemm1,self.gemm2,self.reduce]

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

    def gemm1(self):
        c=self.config
        BM,BN,BK,GM=c['BLOCK_SIZE_M'],c['BLOCK_SIZE_N'],c['BLOCK_SIZE_K'],c['GROUP_SIZE_M']
        EM=min(self.sorted.numel(),self.M*self.k*BM)
        grid=(triton.cdiv(EM,BM)*triton.cdiv(self.N,BN),)
        gemm1_act_kernel[grid](
            self.x,self.w1,self.act,
            self.sorted_ids,self.expert_ids,self.padded,
            self.N,self.K,EM,self.M*self.k,
            self.x.stride(0),self.x.stride(1),
            self.w1.stride(0),self.w1.stride(2),self.w1.stride(1),
            self.act.stride(0),self.act.stride(1),
            top_k=self.k,
            BLOCK_SIZE_M=BM,BLOCK_SIZE_N=BN,BLOCK_SIZE_K=BK,GROUP_SIZE_M=GM,
            num_warps=c.get('num_warps',4),num_stages=c.get('num_stages',3),
        )

    def gemm2(self):self.invoke(self.act,self.w2,self.parts,1,True)

    def reduce(self):
        torch.sum(self.parts,dim=1,out=self.out)

    def __call__(self):
        for f in self.stage_fns:f()
        return self.out
