#!/usr/bin/env python3
"""
Qwen Image API Server Startup Script with Flash Attention Compatibility
"""

import os
import sys

def setup_environment():
    """Setup environment variables for compatibility"""
    # Disable flash attention to avoid C++ compatibility issues
    os.environ["DIFFUSERS_DISABLE_FLASH_ATTENTION"] = "1"
    
    # Additional environment variables for stability
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
    
    # Force CPU attention if flash attention causes issues
    # os.environ["ATTN_IMPLEMENTATION"] = "sdpa"  # Uncomment if still having issues
    
    print("Environment configured for Qwen Image API")
    print(f"DIFFUSERS_DISABLE_FLASH_ATTENTION: {os.environ.get('DIFFUSERS_DISABLE_FLASH_ATTENTION')}")
    print(f"TOKENIZERS_PARALLELISM: {os.environ.get('TOKENIZERS_PARALLELISM')}")

def main():
    """Main startup function"""
    setup_environment()
    
    try:
        # Import main after setting environment variables
        from main import app
        import uvicorn
        
        print("\nStarting Qwen Image Generation API Server...")
        print("Server will be available at: http://localhost:8000")
        print("API Documentation: http://localhost:8000/docs")
        print("Health Check: http://localhost:8000/health")
        
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8000,
            log_level="info"
        )
        
    except ImportError as e:
        print(f"Error importing modules: {e}")
        print("Please ensure all dependencies are installed:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
