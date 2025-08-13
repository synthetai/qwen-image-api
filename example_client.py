#!/usr/bin/env python3
"""
Example client for Qwen Image Generation API
"""

import requests
import base64
import time
import argparse
from PIL import Image
import io

def create_image_task(base_url, prompt, **kwargs):
    """Create an image generation task"""
    data = {"prompt": prompt}
    data.update(kwargs)
    
    response = requests.post(f"{base_url}/v1/images/generations", json=data)
    response.raise_for_status()
    return response.json()

def get_task_status(base_url, task_id):
    """Get task status"""
    response = requests.get(f"{base_url}/v1/images/generations/{task_id}")
    response.raise_for_status()
    return response.json()

def wait_for_completion(base_url, task_id, timeout=300):
    """Wait for task completion"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        task_status = get_task_status(base_url, task_id)
        status = task_status["status"]
        
        print(f"Task status: {status}")
        
        if status == "completed":
            return task_status
        elif status == "failed":
            raise Exception(f"Task failed: {task_status.get('error', 'Unknown error')}")
        
        time.sleep(2)
    
    raise TimeoutError(f"Task did not complete within {timeout} seconds")

def save_image_from_base64(image_base64, filename):
    """Save base64 image to file"""
    image_data = base64.b64decode(image_base64)
    image = Image.open(io.BytesIO(image_data))
    image.save(filename)
    print(f"Image saved as {filename}")

def main():
    parser = argparse.ArgumentParser(description="Qwen Image Generation API Client")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--prompt", required=True, help="Image generation prompt")
    parser.add_argument("--negative-prompt", help="Negative prompt")
    parser.add_argument("--aspect-ratio", default="16:9", help="Aspect ratio")
    parser.add_argument("--steps", type=int, default=50, help="Number of inference steps")
    parser.add_argument("--cfg-scale", type=float, default=4.0, help="CFG scale")
    parser.add_argument("--output", default="generated_image.png", help="Output filename")
    parser.add_argument("--callback-url", help="Callback URL")
    
    args = parser.parse_args()
    
    try:
        # Check health
        print("Checking API health...")
        health_response = requests.get(f"{args.url}/health")
        health_response.raise_for_status()
        health_data = health_response.json()
        print(f"API Status: {health_data['status']}")
        print(f"Model loaded: {health_data['model_loaded']}")
        print(f"Device: {health_data['device']}")
        
        # Create task
        print(f"\nCreating image generation task...")
        print(f"Prompt: {args.prompt}")
        
        task_data = {
            "aspect_ratio": args.aspect_ratio,
            "num_inference_steps": args.steps,
            "true_cfg_scale": args.cfg_scale
        }
        
        if args.negative_prompt:
            task_data["negative_prompt"] = args.negative_prompt
        if args.callback_url:
            task_data["callback_url"] = args.callback_url
        
        task_response = create_image_task(args.url, args.prompt, **task_data)
        task_id = task_response["id"]
        print(f"Task created with ID: {task_id}")
        
        # Wait for completion
        print("\nWaiting for task completion...")
        result = wait_for_completion(args.url, task_id)
        
        # Save image
        image_base64 = result["result"]["image"]
        save_image_from_base64(image_base64, args.output)
        
        # Print result info
        print(f"\nGeneration completed successfully!")
        print(f"Aspect ratio: {result['result']['aspect_ratio']}")
        print(f"Dimensions: {result['result']['width']}x{result['result']['height']}")
        print(f"Steps: {result['result']['num_inference_steps']}")
        print(f"CFG Scale: {result['result']['true_cfg_scale']}")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
