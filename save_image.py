#!/usr/bin/env python3
"""
简单的图片保存脚本，不依赖 jq
用法: python3 save_image.py <task_id> [output_filename]
"""

import sys
import json
import base64
import requests

def save_image_from_task(task_id, output_filename="generated_image.png", api_base="http://localhost:8000"):
    """从任务ID获取并保存图片"""
    try:
        # 获取任务状态
        url = f"{api_base}/v1/images/generations/{task_id}"
        print(f"正在获取任务状态: {url}")
        
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        status = data.get("status")
        
        print(f"任务状态: {status}")
        
        if status == "completed":
            # 获取图片数据
            image_base64 = data["result"]["image"]
            
            # 解码并保存
            image_data = base64.b64decode(image_base64)
            
            with open(output_filename, "wb") as f:
                f.write(image_data)
            
            # 获取文件大小
            import os
            file_size = os.path.getsize(output_filename)
            
            print(f"✅ 图片已保存: {output_filename}")
            print(f"📁 文件大小: {file_size:,} 字节")
            
            # 显示图片信息
            result = data["result"]
            print(f"📋 图片信息:")
            print(f"   提示词: {result.get('prompt', 'N/A')}")
            print(f"   尺寸: {result.get('width', 'N/A')}x{result.get('height', 'N/A')}")
            print(f"   比例: {result.get('aspect_ratio', 'N/A')}")
            print(f"   步数: {result.get('num_inference_steps', 'N/A')}")
            
        elif status == "failed":
            print(f"❌ 任务失败: {data.get('error', '未知错误')}")
            return False
        elif status in ["pending", "processing"]:
            print(f"⏳ 任务还在处理中，请稍后再试")
            return False
        else:
            print(f"❓ 未知状态: {status}")
            return False
            
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求错误: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python3 save_image.py <task_id> [output_filename] [api_base]")
        print("示例: python3 save_image.py 2f9ef721-2eeb-4bc5-a72c-faba2c69e78b my_image.png")
        print("示例: python3 save_image.py 2f9ef721-2eeb-4bc5-a72c-faba2c69e78b my_image.png http://localhost:7860")
        sys.exit(1)
    
    task_id = sys.argv[1]
    output_filename = sys.argv[2] if len(sys.argv) > 2 else "generated_image.png"
    api_base = sys.argv[3] if len(sys.argv) > 3 else "http://localhost:8000"
    
    print(f"🎯 任务ID: {task_id}")
    print(f"📁 输出文件: {output_filename}")
    print(f"🌐 API地址: {api_base}")
    print("-" * 50)
    
    success = save_image_from_task(task_id, output_filename, api_base)
    
    if success:
        print(f"\n🎉 完成！图片已保存为: {output_filename}")
    else:
        print(f"\n❌ 保存失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
