import asyncio
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
import base64
import io
import logging
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
import os

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import torch

# Disable flash attention to avoid compatibility issues
os.environ["DIFFUSERS_DISABLE_FLASH_ATTENTION"] = "1"

from diffusers import DiffusionPipeline
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for the model
pipe = None
device = None
torch_dtype = None

# Task storage (in production, use a database)
tasks: Dict[str, Dict[str, Any]] = {}

# Thread pool for image generation
executor = ThreadPoolExecutor(max_workers=2)

def setup_environment():
    """Setup environment variables for compatibility"""
    # Disable flash attention to avoid C++ compatibility issues
    os.environ["DIFFUSERS_DISABLE_FLASH_ATTENTION"] = "1"
    
    # Additional environment variables for stability
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
    
    logger.info("Environment configured for Qwen Image API")
    logger.info(f"DIFFUSERS_DISABLE_FLASH_ATTENTION: {os.environ.get('DIFFUSERS_DISABLE_FLASH_ATTENTION')}")
    logger.info(f"TOKENIZERS_PARALLELISM: {os.environ.get('TOKENIZERS_PARALLELISM')}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global pipe, device, torch_dtype
    
    # Setup environment first
    setup_environment()
    
    logger.info("Initializing Qwen Image model...")
    model_name = "Qwen/Qwen-Image"
    
    # Load the pipeline
    if torch.cuda.is_available():
        torch_dtype = torch.bfloat16
        device = "cuda"
    else:
        torch_dtype = torch.float32
        device = "cpu"
    
    pipe = DiffusionPipeline.from_pretrained(model_name, torch_dtype=torch_dtype)
    pipe = pipe.to(device)
    logger.info(f"Model loaded successfully on device: {device}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    executor.shutdown(wait=True)

app = FastAPI(
    title="Qwen Image Generation API",
    description="API for generating images using Qwen/Qwen-Image model",
    version="1.0.0",
    lifespan=lifespan
)

# Pydantic models
class ImageGenerationRequest(BaseModel):
    prompt: str = Field(..., description="Text prompt for image generation")
    negative_prompt: Optional[str] = Field(" ", description="Negative prompt (optional)")
    aspect_ratio: str = Field("16:9", description="Image aspect ratio")
    num_inference_steps: int = Field(50, description="Number of inference steps")
    true_cfg_scale: float = Field(4.0, description="CFG scale value")
    callback_url: Optional[str] = Field(None, description="Callback URL for task completion")

class ImageGenerationResponse(BaseModel):
    id: str
    status: str
    created_at: str
    
class TaskStatusResponse(BaseModel):
    id: str
    status: str
    created_at: str
    completed_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Constants
POSITIVE_MAGIC = {
    "en": "Ultra HD, 4K, cinematic composition.",
    "zh": "超清，4K，电影级构图"
}

ASPECT_RATIOS = {
    "1:1": (1328, 1328),
    "16:9": (1664, 928),
    "9:16": (928, 1664),
    "4:3": (1472, 1104),
    "3:4": (1104, 1472),
    "3:2": (1584, 1056),
    "2:3": (1056, 1584),
}

def detect_language(text: str) -> str:
    """Simple language detection"""
    # Check if text contains Chinese characters
    for char in text:
        if '\u4e00' <= char <= '\u9fff':
            return "zh"
    return "en"

def image_to_base64(image) -> str:
    """Convert PIL image to base64 string"""
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    return image_base64

async def send_callback(callback_url: str, task_data: Dict[str, Any]):
    """Send callback notification"""
    try:
        response = requests.post(callback_url, json=task_data, timeout=30)
        logger.info(f"Callback sent to {callback_url}, status: {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to send callback to {callback_url}: {str(e)}")

def generate_image_sync(task_id: str, request_data: ImageGenerationRequest):
    """Synchronous image generation function"""
    try:
        logger.info(f"Starting image generation for task {task_id}")
        
        # Update task status
        tasks[task_id]["status"] = "processing"
        
        # Prepare parameters
        prompt = request_data.prompt
        negative_prompt = request_data.negative_prompt or " "
        aspect_ratio = request_data.aspect_ratio
        num_inference_steps = request_data.num_inference_steps
        true_cfg_scale = request_data.true_cfg_scale
        
        # Validate aspect ratio
        if aspect_ratio not in ASPECT_RATIOS:
            raise ValueError(f"Invalid aspect ratio. Supported ratios: {list(ASPECT_RATIOS.keys())}")
        
        width, height = ASPECT_RATIOS[aspect_ratio]
        
        # Detect language and add positive magic
        lang = detect_language(prompt)
        final_prompt = prompt + " " + POSITIVE_MAGIC[lang]
        
        # Generate image
        generator = torch.Generator(device=device).manual_seed(42)
        image = pipe(
            prompt=final_prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            num_inference_steps=num_inference_steps,
            true_cfg_scale=true_cfg_scale,
            generator=generator
        ).images[0]
        
        # Convert to base64
        image_base64 = image_to_base64(image)
        
        # Update task with result
        completed_at = datetime.utcnow().isoformat()
        tasks[task_id].update({
            "status": "completed",
            "completed_at": completed_at,
            "result": {
                "image": image_base64,
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "aspect_ratio": aspect_ratio,
                "num_inference_steps": num_inference_steps,
                "true_cfg_scale": true_cfg_scale,
                "width": width,
                "height": height
            }
        })
        
        logger.info(f"Image generation completed for task {task_id}")
        
        # Send callback if provided
        if request_data.callback_url:
            asyncio.create_task(send_callback(request_data.callback_url, tasks[task_id]))
            
    except Exception as e:
        logger.error(f"Image generation failed for task {task_id}: {str(e)}")
        tasks[task_id].update({
            "status": "failed",
            "completed_at": datetime.utcnow().isoformat(),
            "error": str(e)
        })
        
        # Send callback with error if provided
        if request_data.callback_url:
            asyncio.create_task(send_callback(request_data.callback_url, tasks[task_id]))

async def generate_image_async(task_id: str, request_data: ImageGenerationRequest):
    """Async wrapper for image generation"""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, generate_image_sync, task_id, request_data)

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": pipe is not None,
        "device": device,
        "torch_dtype": str(torch_dtype) if torch_dtype else None,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/v1/images/generations", response_model=ImageGenerationResponse)
async def create_image_generation(
    request: ImageGenerationRequest,
    background_tasks: BackgroundTasks
):
    """Create an image generation task"""
    
    # Validate aspect ratio
    if request.aspect_ratio not in ASPECT_RATIOS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid aspect ratio. Supported ratios: {list(ASPECT_RATIOS.keys())}"
        )
    
    # Generate task ID
    task_id = str(uuid.uuid4())
    
    # Create task record
    task_data = {
        "id": task_id,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
        "request": request.dict()
    }
    tasks[task_id] = task_data
    
    # Start background task
    background_tasks.add_task(generate_image_async, task_id, request)
    
    return ImageGenerationResponse(
        id=task_id,
        status="pending",
        created_at=task_data["created_at"]
    )

@app.get("/v1/images/generations/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Get the status of an image generation task"""
    
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_data = tasks[task_id]
    
    return TaskStatusResponse(
        id=task_data["id"],
        status=task_data["status"],
        created_at=task_data["created_at"],
        completed_at=task_data.get("completed_at"),
        result=task_data.get("result"),
        error=task_data.get("error")
    )

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Qwen Image Generation API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "create_task": "/v1/images/generations",
            "get_task": "/v1/images/generations/{id}"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
