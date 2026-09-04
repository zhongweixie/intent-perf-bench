# Container Images

## pytorch_cutile.sif

**大小**: 9.1GB  
**用途**: PyTorch + CUTLASS 集成环境，用于运行 CUDA kernel 优化任务

### 任务依赖

以下任务需要此容器：
- `ipb_cuda_001` - CUDA Matrix Multiplication
- `ipb_cuda_006_flash_attention_cutile` - Flash Attention (CuTiLe)
- `ipb_cuda_008_conv1d_shared` - 1D Convolution with Shared Memory
- `ipb_cuda_009_matrix_transpose` - Matrix Transpose
- `ipb_cuda_010_layernorm` - Layer Normalization
- 其他 CUDA kernel 优化任务

### 构建方法

**选项 1: 使用 Singularity Definition File**

```bash
# 如果你有 Singularity 定义文件
sudo singularity build pytorch_cutile.sif pytorch_cutile.def
```

**选项 2: 从 Docker 转换**

```bash
# 从 Docker Hub 拉取并转换
singularity pull docker://pytorch/pytorch:2.1.0-cuda12.1-cudnn8-devel

# 或使用自定义 Dockerfile
docker build -t pytorch_cutile:latest .
singularity build pytorch_cutile.sif docker-daemon://pytorch_cutile:latest
```

**选项 3: 直接下载（如果有托管）**

```bash
# 待补充：容器托管链接
# wget https://example.com/pytorch_cutile.sif
```

### 环境说明

容器包含：
- **PyTorch**: 2.x (CUDA 支持)
- **CUDA Toolkit**: 12.x
- **CuTiLe**: NVIDIA CUTLASS Template Library
- **Python**: 3.10
- **其他依赖**: numpy, scipy, pandas 等

### 使用方法

```bash
# 以交互方式运行
singularity shell --nv containers/pytorch_cutile.sif

# 执行脚本
singularity exec --nv containers/pytorch_cutile.sif python script.py

# 在 SLURM 作业中使用
srun --gres=gpu:1 singularity exec --nv containers/pytorch_cutile.sif \
    python ipb_exec.py --task ipb_cuda_001
```

### 不需要容器的任务

纯 Python/CPU 任务（ipb_dev_* 系列）使用标准 Python 环境即可：

```bash
pip install -r requirements.txt
```

## 其他容器

如果未来需要其他特殊环境（如 TensorFlow、JAX），在此补充说明。
