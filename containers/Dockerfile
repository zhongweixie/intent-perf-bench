FROM nvcr.io/nvidia/pytorch:26.04-py3

LABEL maintainer="Intent-Perf-Bench"
LABEL description="PyTorch + CUDA + CuTile environment for IPB CUDA tasks"

# Install cuda-tile
RUN pip install --upgrade cuda-tile==1.5.0

# Set working directory
WORKDIR /workspace

# Verify installation
RUN python -c "import torch; import cuda_tile; print(f'PyTorch {torch.__version__}, CUDA {torch.version.cuda}, cuda-tile {cuda_tile.__version__}')"
