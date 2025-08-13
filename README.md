# Qwen Image Generation API

基于 Qwen/Qwen-Image 模型的图片生成 API 服务。

## 功能特性

- 支持中英文提示词生成图片
- 多种图片宽高比支持
- 异步任务处理
- 任务状态查询
- 回调通知功能
- 健康检查接口

## 安装和运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

**重要依赖说明：**
- **transformers>=4.51.3**：支持 Qwen2.5-VL 模型
- **diffusers**：使用最新的 GitHub 版本以获得最佳兼容性
- **fastapi>=0.115.2**：解决与 gradio 的依赖冲突
- **pydantic>=2.9.2**：解决与 albumentations 的依赖冲突

**解决依赖冲突：**
如果您的环境中已安装 gradio 或 albumentations，可能会遇到依赖冲突警告。这些警告不会影响 API 正常运行，但如果您希望完全解决，可以：

1. **升级所有包到兼容版本（推荐）：**
```bash
pip install --upgrade -r requirements.txt
```

2. **如果遇到问题，可以手动安装最新版本：**
```bash
pip install transformers>=4.51.3
pip install git+https://github.com/huggingface/diffusers
pip install fastapi>=0.115.2 pydantic>=2.9.2
```

3. **创建新的虚拟环境（最彻底的解决方案）：**
```bash
python -m venv qwen_api_env
source qwen_api_env/bin/activate  # Linux/Mac
# 或 qwen_api_env\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. 运行服务

**推荐使用启动脚本（自动处理兼容性问题）：**
```bash
python start_server.py
```

**或者直接运行：**
```bash
python main.py
```

**或使用 uvicorn：**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

服务将在 `http://localhost:8000` 启动。

### 3. 常见问题解决

#### Flash Attention 兼容性问题

如果遇到 `flash_attn` 相关的错误（如 `undefined symbol` 错误），这是由于 flash attention 库与当前 PyTorch 版本不兼容导致的。解决方案：

**方案一（推荐）：使用启动脚本**
```bash
python start_server.py
```
启动脚本会自动禁用 flash attention，使用标准的注意力机制。

**方案二：手动设置环境变量**
```bash
export DIFFUSERS_DISABLE_FLASH_ATTENTION=1
python main.py
```

**方案三：卸载 flash attention**
```bash
pip uninstall flash-attn
python main.py
```

**方案四：重新编译 flash attention**
```bash
pip uninstall flash-attn
pip install flash-attn --no-build-isolation --force-reinstall
```

#### CUDA 内存不足
如果遇到 CUDA 内存不足的问题：
```bash
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
python start_server.py
```

## API 接口

### 健康检查

```http
GET /health
```

响应示例:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "device": "cuda",
  "torch_dtype": "torch.bfloat16",
  "timestamp": "2024-01-01T12:00:00"
}
```

### 创建图片生成任务

```http
POST /v1/images/generations
Content-Type: application/json
```

请求参数:
- `prompt` (必填): 文生图的提示词
- `negative_prompt` (可选): 负向提示词，默认为空格
- `aspect_ratio` (可选): 图片比例，默认 "16:9"
- `num_inference_steps` (可选): 生成步数，默认 50
- `true_cfg_scale` (可选): CFG 缩放值，默认 4.0
- `callback_url` (可选): 任务完成后的回调 URL

支持的图片比例:
- "1:1" (1328x1328)
- "16:9" (1664x928) - 默认
- "9:16" (928x1664)
- "4:3" (1472x1104)
- "3:4" (1104x1472)
- "3:2" (1584x1056)
- "2:3" (1056x1584)

请求示例:
```json
{
  "prompt": "A beautiful landscape with mountains and lakes",
  "negative_prompt": "blurry, low quality",
  "aspect_ratio": "16:9",
  "num_inference_steps": 50,
  "true_cfg_scale": 4.0,
  "callback_url": "https://your-domain.com/callback"
}
```

响应示例:
```json
{
  "id": "uuid-task-id",
  "status": "pending",
  "created_at": "2024-01-01T12:00:00"
}
```

### 查询任务状态

```http
GET /v1/images/generations/{task_id}
```

响应示例:

**处理中:**
```json
{
  "id": "uuid-task-id",
  "status": "processing",
  "created_at": "2024-01-01T12:00:00",
  "completed_at": null,
  "result": null,
  "error": null
}
```

**完成:**
```json
{
  "id": "uuid-task-id",
  "status": "completed",
  "created_at": "2024-01-01T12:00:00",
  "completed_at": "2024-01-01T12:01:00",
  "result": {
    "image": "base64-encoded-image",
    "prompt": "A beautiful landscape with mountains and lakes",
    "negative_prompt": "blurry, low quality",
    "aspect_ratio": "16:9",
    "num_inference_steps": 50,
    "true_cfg_scale": 4.0,
    "width": 1664,
    "height": 928
  },
  "error": null
}
```

**失败:**
```json
{
  "id": "uuid-task-id",
  "status": "failed",
  "created_at": "2024-01-01T12:00:00",
  "completed_at": "2024-01-01T12:01:00",
  "result": null,
  "error": "Error message"
}
```

## 使用示例

### Python 客户端示例

```python
import requests
import base64
import time
from PIL import Image
import io

# API 基础 URL
BASE_URL = "http://localhost:8000"

# 创建任务
response = requests.post(f"{BASE_URL}/v1/images/generations", json={
    "prompt": "一只可爱的小猫在花园里玩耍",
    "aspect_ratio": "1:1",
    "num_inference_steps": 30
})

task_data = response.json()
task_id = task_data["id"]
print(f"任务已创建，ID: {task_id}")

# 轮询任务状态
while True:
    response = requests.get(f"{BASE_URL}/v1/images/generations/{task_id}")
    task_status = response.json()
    
    if task_status["status"] == "completed":
        # 获取图片
        image_base64 = task_status["result"]["image"]
        image_data = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_data))
        image.save("generated_image.png")
        print("图片已保存为 generated_image.png")
        break
    elif task_status["status"] == "failed":
        print(f"任务失败: {task_status['error']}")
        break
    else:
        print(f"任务状态: {task_status['status']}")
        time.sleep(2)
```

### curl 示例

```bash
# 创建任务
curl -X POST "http://localhost:8000/v1/images/generations" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A coffee shop entrance with a chalkboard sign",
    "aspect_ratio": "16:9"
  }'

# 查询任务状态
curl "http://localhost:8000/v1/images/generations/{task_id}"
```

## 技术细节

- **框架**: FastAPI
- **模型**: Qwen/Qwen-Image
- **推理后端**: PyTorch + Diffusers
- **并发处理**: 异步任务队列
- **图片格式**: PNG (Base64 编码)

## 注意事项

1. 首次运行时会下载模型文件，请确保网络连接正常
2. GPU 环境下性能更佳，会自动检测并使用 CUDA
3. 生成时间根据步数和硬件配置而定，通常在 10-60 秒之间
4. 当前使用内存存储任务状态，重启服务后任务记录会丢失
5. 生产环境建议使用数据库存储任务状态，并配置负载均衡

## License

MIT
