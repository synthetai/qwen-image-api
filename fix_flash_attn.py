#!/usr/bin/env python3
"""
Flash Attention Cleanup Script for Server Environment
在服务器上运行此脚本来彻底清理 flash attention 相关问题
"""

import os
import sys
import subprocess
import glob
import shutil

def run_command(cmd):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def find_python_packages_dir():
    """查找 Python 包安装目录"""
    try:
        import site
        site_packages = site.getsitepackages()
        
        # 检查常见的包目录
        possible_dirs = [
            "/usr/local/lib/python3.10/dist-packages",
            "/usr/local/lib/python3.10/site-packages", 
            "/opt/conda/lib/python3.10/site-packages",
            "/home/user/.local/lib/python3.10/site-packages"
        ]
        
        # 添加 site.getsitepackages() 返回的目录
        possible_dirs.extend(site_packages)
        
        existing_dirs = []
        for dir_path in possible_dirs:
            if os.path.exists(dir_path):
                existing_dirs.append(dir_path)
        
        return existing_dirs
    except Exception as e:
        print(f"Error finding packages directory: {e}")
        return []

def find_flash_attn_files():
    """查找所有 flash attention 相关文件"""
    package_dirs = find_python_packages_dir()
    flash_files = []
    
    for pkg_dir in package_dirs:
        if os.path.exists(pkg_dir):
            print(f"Searching in: {pkg_dir}")
            
            # 查找 flash_attn 相关文件
            patterns = [
                os.path.join(pkg_dir, "*flash_attn*"),
                os.path.join(pkg_dir, "flash_attn*"),
                os.path.join(pkg_dir, "**/*flash_attn*")
            ]
            
            for pattern in patterns:
                files = glob.glob(pattern, recursive=True)
                flash_files.extend(files)
    
    return list(set(flash_files))  # 去重

def cleanup_flash_attn():
    """清理 flash attention 文件"""
    print("🧹 Starting flash attention cleanup...")
    
    # 1. 使用 pip 卸载
    print("\n1. Uninstalling flash-attn with pip...")
    success, stdout, stderr = run_command("pip uninstall flash-attn -y")
    if success:
        print("✅ pip uninstall successful")
    else:
        print(f"⚠️  pip uninstall failed or package not found: {stderr}")
    
    # 2. 查找并删除残留文件
    print("\n2. Finding and removing remaining files...")
    flash_files = find_flash_attn_files()
    
    if flash_files:
        print(f"Found {len(flash_files)} flash attention related files:")
        for file_path in flash_files:
            print(f"  - {file_path}")
        
        print("\nRemoving files...")
        for file_path in flash_files:
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"✅ Removed file: {file_path}")
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                    print(f"✅ Removed directory: {file_path}")
            except Exception as e:
                print(f"❌ Failed to remove {file_path}: {e}")
    else:
        print("No flash attention files found")
    
    # 3. 清理 pip 缓存
    print("\n3. Clearing pip cache...")
    success, stdout, stderr = run_command("pip cache purge")
    if success:
        print("✅ pip cache cleared")
    else:
        print(f"⚠️  Failed to clear pip cache: {stderr}")

def test_diffusers_import():
    """测试 diffusers 导入"""
    print("\n4. Testing diffusers import...")
    
    # 设置环境变量
    os.environ["DIFFUSERS_DISABLE_FLASH_ATTENTION"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    
    try:
        # 清理已导入的模块
        modules_to_remove = [key for key in sys.modules.keys() if 'diffusers' in key or 'flash' in key]
        for module in modules_to_remove:
            del sys.modules[module]
        
        from diffusers import DiffusionPipeline
        print("✅ Diffusers import successful!")
        return True
    except Exception as e:
        print(f"❌ Diffusers import failed: {e}")
        return False

def main():
    """主函数"""
    print("🔧 Flash Attention Fix Script for Server")
    print("=" * 50)
    
    # 检查是否有管理员权限
    if os.geteuid() != 0:
        print("⚠️  Warning: Running without sudo. Some files may not be removable.")
        print("If cleanup fails, try running with sudo:")
        print("sudo python3 fix_flash_attn.py")
        print()
    
    cleanup_flash_attn()
    
    if test_diffusers_import():
        print("\n🎉 Flash attention cleanup successful!")
        print("You can now run: python3 start_server.py")
    else:
        print("\n💡 Additional steps needed:")
        print("1. Try reinstalling diffusers:")
        print("   pip uninstall diffusers -y")
        print("   pip install git+https://github.com/huggingface/diffusers")
        print("2. Or try using a different PyTorch version:")
        print("   pip install torch==2.1.0 torchvision==0.16.0")

if __name__ == "__main__":
    main()
