#!/usr/bin/env python3
"""
Environment Check Script for Qwen Image API
"""

import sys
import os

def check_python_version():
    """Check Python version"""
    print(f"Python version: {sys.version}")
    if sys.version_info < (3, 8):
        print("❌ Warning: Python 3.8+ is recommended")
    else:
        print("✅ Python version is compatible")

def check_packages():
    """Check if required packages can be imported"""
    packages = {
        'torch': 'PyTorch',
        'transformers': 'Transformers',
        'fastapi': 'FastAPI',
        'pydantic': 'Pydantic',
        'PIL': 'Pillow',
        'requests': 'Requests'
    }
    
    print("\nChecking package imports:")
    for package, name in packages.items():
        try:
            __import__(package)
            print(f"✅ {name}: OK")
        except ImportError as e:
            print(f"❌ {name}: FAILED - {e}")

def check_torch():
    """Check PyTorch configuration"""
    try:
        import torch
        print(f"\nPyTorch version: {torch.__version__}")
        print(f"CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"CUDA version: {torch.version.cuda}")
            print(f"GPU count: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
        print("✅ PyTorch: OK")
    except Exception as e:
        print(f"❌ PyTorch check failed: {e}")

def check_diffusers():
    """Check diffusers import with flash attention disabled"""
    print("\nChecking diffusers import...")
    
    # Set environment variable to disable flash attention
    os.environ["DIFFUSERS_DISABLE_FLASH_ATTENTION"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    
    try:
        from diffusers import DiffusionPipeline
        print("✅ Diffusers import: OK")
        
        # Try to get pipeline info (without loading the model)
        print("✅ DiffusionPipeline accessible: OK")
        
    except Exception as e:
        print(f"❌ Diffusers check failed: {e}")
        print("Suggestion: Try uninstalling flash-attn:")
        print("pip uninstall flash-attn")

def check_flash_attention():
    """Check flash attention status"""
    print("\nChecking flash attention...")
    try:
        import flash_attn
        print(f"Flash attention version: {flash_attn.__version__}")
        print("⚠️  Flash attention is installed but may cause compatibility issues")
        print("Consider uninstalling if you encounter import errors:")
        print("pip uninstall flash-attn")
    except ImportError:
        print("✅ Flash attention not installed (this is good for compatibility)")

def main():
    """Main check function"""
    print("🔍 Qwen Image API Environment Check")
    print("=" * 50)
    
    check_python_version()
    check_packages()
    check_torch()
    check_flash_attention()
    check_diffusers()
    
    print("\n" + "=" * 50)
    print("Environment check completed!")
    print("\nIf all checks pass, you can try running:")
    print("python start_server.py")

if __name__ == "__main__":
    main()
