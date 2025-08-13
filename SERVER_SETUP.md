# 服务器部署指南

## 🚨 Flash Attention 问题解决

根据您遇到的错误，请在服务器上按以下步骤操作：

### 步骤 1：清理 Flash Attention 残留文件

```bash
# 卸载 flash-attn
pip uninstall flash-attn -y

# 手动删除残留文件
sudo rm -rf /usr/local/lib/python3.10/dist-packages/*flash_attn*
sudo rm -rf /usr/local/lib/python3.10/dist-packages/flash_attn*

# 清理 pip 缓存
pip cache purge
```

### 步骤 2：重新安装 diffusers

```bash
# 卸载并重新安装 diffusers
pip uninstall diffusers -y
pip install git+https://github.com/huggingface/diffusers
```

### 步骤 3：启动服务

```bash
# 直接启动（已集成环境配置）
python3 main.py

# 或者手动设置环境变量启动
export DIFFUSERS_DISABLE_FLASH_ATTENTION=1
export TOKENIZERS_PARALLELISM=false
python3 main.py
```

## 🔍 问题诊断

如果仍有问题，可以运行：

```bash
# 检查环境
python3 check_environment.py

# 查看详细错误信息
python3 -c "
import os
os.environ['DIFFUSERS_DISABLE_FLASH_ATTENTION'] = '1'
from diffusers import DiffusionPipeline
print('Success!')
"
```

## 📝 常见问题

### 问题 1：权限不够
```bash
# 使用 sudo 运行清理脚本
sudo python3 fix_flash_attn.py
```

### 问题 2：PyTorch 版本冲突
```bash
# 降级到稳定版本
pip install torch==2.1.0 torchvision==0.16.0
pip install git+https://github.com/huggingface/diffusers
```

### 问题 3：CUDA 内存不足
```bash
# 设置内存分配策略
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
python3 start_server.py
```

## 🚀 验证部署

服务启动后，可以通过以下方式验证：

```bash
# 健康检查
curl http://localhost:8000/health

# 查看 API 文档
curl http://localhost:8000/docs
```



## 📞 技术支持

如果以上步骤仍无法解决问题，请提供：
1. 操作系统版本
2. Python 版本
3. PyTorch 版本  
4. CUDA 版本
5. 完整的错误日志
