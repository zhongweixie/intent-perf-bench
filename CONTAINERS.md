# Container Images

## pytorch_cutile - PyTorch + CUDA + CuTile 环境

**用途**: PyTorch + CUTLASS 集成环境，用于运行 CUDA kernel 优化任务

### 任务依赖

以下任务需要此容器：
- `ipb_cuda_001` - CUDA Matrix Multiplication
- `ipb_cuda_006_flash_attention_cutile` - Flash Attention (CuTiLe)
- `ipb_cuda_008_conv1d_shared` - 1D Convolution with Shared Memory
- `ipb_cuda_009_matrix_transpose` - Matrix Transpose
- `ipb_cuda_010_layernorm` - Layer Normalization

### 快速开始

**选项 1: 下载预构建的 Singularity 容器** (推荐，HPC环境)

```bash
# 从 OneDrive 下载 (9.1 GB)
wget "https://hkustconnect-my.sharepoint.com/personal/zxiebk_connect_ust_hk/_layouts/15/download.aspx?share=IQDbaDspfcxLQZGsKHx9hv-GAdtBT9Vvnk737xMQz3ny0Lo" \
  -O pytorch_cutile.sif

# 或使用 rclone (如果已配置)
rclone copy onedrive:/intent-perf-bench-containers/pytorch_cutile.sif .

# 移动到项目目录
mv pytorch_cutile.sif containers/

# 使用容器
singularity exec --nv containers/pytorch_cutile.sif \
  python evaluation/evaluate.py --task-id ipb_cuda_001
```

**选项 2: 使用 Docker** (需要自行构建)

```bash
# 从 Dockerfile 构建
cd containers/
docker build -t pytorch-cutile:local -f Dockerfile .

# 运行
docker run --gpus all -it --rm \
  -v $(pwd):/workspace \
  pytorch-cutile:local bash
```

**选项 3: 转换为 Singularity (HPC 环境)**

```bash
# 从 Docker Hub 转换
singularity pull docker://zwxie/codebench:pytorch-cutile-v1.0

# 使用
singularity exec --nv pytorch-cutile-v1.0.sif python script.py

# 在 SLURM 作业中使用
srun --gres=gpu:1 singularity exec --nv pytorch-cutile-v1.0.sif \
    python evaluation/evaluate.py --task ipb_cuda_001
```

### 环境说明

容器基于 `nvcr.io/nvidia/pytorch:26.04-py3`，包含：
- **PyTorch**: 2.x (CUDA 支持)
- **CUDA Toolkit**: 12.x
- **CuTile**: 1.5.0 (NVIDIA CUTLASS Template Library)
- **Python**: 3.10

### 不需要容器的任务

纯 Python/CPU 任务（ipb_dev_* 系列）使用标准 Python 环境即可：

```bash
pip install -r requirements.txt
```

## 其他容器

如果未来需要其他特殊环境（如 TensorFlow、JAX），在此补充说明。
