FROM nvidia/cuda:12.4-devel-ubuntu22.04

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 禁用 flash attention 避免兼容性问题
ENV DIFFUSERS_DISABLE_FLASH_ATTENTION=1
ENV TOKENIZERS_PARALLELISM=false
ENV HF_HUB_DISABLE_PROGRESS_BARS=1

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-dev \
    python3-pip \
    git \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s /usr/bin/python3.10 /usr/bin/python

# 升级 pip
RUN python -m pip install --no-cache-dir --upgrade pip

# 安装 PyTorch (CUDA 12.4 版本)
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# 复制 requirements.txt 并安装其他 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY main.py .
COPY curl_examples.sh .
COPY check_environment.py .

# 给脚本添加执行权限
RUN chmod +x curl_examples.sh

# 创建非 root 用户
RUN useradd -m -u 1000 qwen && chown -R qwen:qwen /app
USER qwen

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["python", "main.py"]
