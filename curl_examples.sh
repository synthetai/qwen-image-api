#!/bin/bash

# Qwen Image API - Curl 使用示例脚本
# 使用方法：bash curl_examples.sh

API_BASE="http://localhost:8000"

echo "🎯 Qwen Image API - Curl 使用示例"
echo "================================="

# 函数：健康检查
health_check() {
    echo "📊 健康检查..."
    curl -s "${API_BASE}/health" | jq '.'
    echo ""
}

# 函数：创建图片生成任务
create_task() {
    echo "🎨 创建图片生成任务..."
    
    # 你可以修改这里的参数
    PROMPT="一只可爱的小猫在花园里玩耍，阳光明媚，超清，4K画质"
    NEGATIVE_PROMPT="模糊，低质量，变形"
    ASPECT_RATIO="16:9"
    STEPS=30
    CFG_SCALE=4.0
    
    TASK_ID=$(curl -s -X POST "${API_BASE}/v1/images/generations" \
        -H "Content-Type: application/json" \
        -d "{
            \"prompt\": \"${PROMPT}\",
            \"negative_prompt\": \"${NEGATIVE_PROMPT}\",
            \"aspect_ratio\": \"${ASPECT_RATIO}\",
            \"num_inference_steps\": ${STEPS},
            \"true_cfg_scale\": ${CFG_SCALE}
        }" | jq -r '.id')
    
    echo "任务已创建，ID: ${TASK_ID}"
    echo ""
    
    # 返回任务ID供后续使用
    echo "${TASK_ID}"
}

# 函数：查询任务状态并保存图片
check_and_save() {
    local TASK_ID=$1
    local OUTPUT_FILE=${2:-"generated_image.png"}
    
    echo "🔍 查询任务状态: ${TASK_ID}"
    
    # 如果有 jq，使用 jq；否则使用 Python 脚本
    if [ "$USE_PYTHON_FALLBACK" = "1" ]; then
        echo "使用 Python 脚本保存图片..."
        python3 save_image.py "${TASK_ID}" "${OUTPUT_FILE}" "${API_BASE}"
        return
    fi
    
    # 轮询任务状态
    while true; do
        RESPONSE=$(curl -s "${API_BASE}/v1/images/generations/${TASK_ID}")
        STATUS=$(echo "${RESPONSE}" | jq -r '.status')
        
        echo "当前状态: ${STATUS}"
        
        case "${STATUS}" in
            "completed")
                echo "✅ 任务完成！正在保存图片..."
                
                # 提取 base64 图片数据并保存
                echo "${RESPONSE}" | jq -r '.result.image' | base64 -d > "${OUTPUT_FILE}"
                
                if [ -f "${OUTPUT_FILE}" ]; then
                    FILE_SIZE=$(ls -lh "${OUTPUT_FILE}" | awk '{print $5}')
                    echo "🎉 图片已保存: ${OUTPUT_FILE} (${FILE_SIZE})"
                    
                    # 显示图片信息
                    echo ""
                    echo "📋 图片信息:"
                    echo "${RESPONSE}" | jq '.result | {prompt, aspect_ratio, width, height, num_inference_steps, true_cfg_scale}'
                else
                    echo "❌ 图片保存失败"
                fi
                break
                ;;
            "failed")
                echo "❌ 任务失败:"
                echo "${RESPONSE}" | jq '.error'
                break
                ;;
            "processing"|"pending")
                echo "⏳ 任务处理中，等待 3 秒后重试..."
                sleep 3
                ;;
            *)
                echo "❓ 未知状态: ${STATUS}"
                break
                ;;
        esac
    done
}

# 函数：完整流程示例
full_example() {
    echo "🚀 完整示例流程"
    echo "---------------"
    
    # 1. 健康检查
    health_check
    
    # 2. 创建任务
    TASK_ID=$(create_task)
    
    # 3. 查询并保存
    if [ ! -z "${TASK_ID}" ] && [ "${TASK_ID}" != "null" ]; then
        check_and_save "${TASK_ID}" "my_generated_image.png"
    else
        echo "❌ 任务创建失败"
    fi
}

# 函数：自定义生成
custom_generate() {
    echo "✨ 自定义图片生成"
    echo "----------------"
    
    # 读取用户输入
    read -p "请输入提示词: " USER_PROMPT
    read -p "请输入负向提示词 (可选): " USER_NEGATIVE
    read -p "请输入图片比例 (默认 16:9): " USER_RATIO
    read -p "请输入输出文件名 (默认 custom.png): " USER_OUTPUT
    
    # 设置默认值
    USER_RATIO=${USER_RATIO:-"16:9"}
    USER_OUTPUT=${USER_OUTPUT:-"custom.png"}
    
    # 创建任务
    TASK_ID=$(curl -s -X POST "${API_BASE}/v1/images/generations" \
        -H "Content-Type: application/json" \
        -d "{
            \"prompt\": \"${USER_PROMPT}\",
            \"negative_prompt\": \"${USER_NEGATIVE}\",
            \"aspect_ratio\": \"${USER_RATIO}\",
            \"num_inference_steps\": 30,
            \"true_cfg_scale\": 4.0
        }" | jq -r '.id')
    
    echo "任务已创建，ID: ${TASK_ID}"
    
    # 查询并保存
    if [ ! -z "${TASK_ID}" ] && [ "${TASK_ID}" != "null" ]; then
        check_and_save "${TASK_ID}" "${USER_OUTPUT}"
    else
        echo "❌ 任务创建失败"
    fi
}

# 显示帮助
show_help() {
    echo "使用方法:"
    echo "  bash curl_examples.sh [选项]"
    echo ""
    echo "选项:"
    echo "  health          - 仅进行健康检查"
    echo "  create          - 仅创建任务"
    echo "  check <task_id> - 检查指定任务状态"
    echo "  custom          - 自定义图片生成"
    echo "  full            - 完整示例流程 (默认)"
    echo "  help            - 显示此帮助"
    echo ""
    echo "示例:"
    echo "  bash curl_examples.sh health"
    echo "  bash curl_examples.sh custom"
    echo "  bash curl_examples.sh check abc123def"
}

# 检查依赖
check_dependencies() {
    if ! command -v curl &> /dev/null; then
        echo "❌ 需要安装 curl"
        exit 1
    fi
    
    # jq 是可选的，如果没有会提供替代方案
    if ! command -v jq &> /dev/null; then
        echo "⚠️  jq 未安装，将使用 Python 脚本作为替代方案"
        echo "如需安装 jq: sudo apt-get install jq  # Ubuntu/Debian"
        echo "            brew install jq          # macOS"
        USE_PYTHON_FALLBACK=1
    else
        USE_PYTHON_FALLBACK=0
    fi
    
    if ! command -v python3 &> /dev/null; then
        echo "❌ 需要安装 python3"
        exit 1
    fi
}

# 主程序
main() {
    # 检查依赖
    check_dependencies
    
    # 根据参数执行不同功能
    case "${1:-full}" in
        "health")
            health_check
            ;;
        "create")
            create_task
            ;;
        "check")
            if [ -z "$2" ]; then
                echo "❌ 请提供任务ID"
                echo "用法: bash curl_examples.sh check <task_id>"
                exit 1
            fi
            check_and_save "$2" "${3:-generated.png}"
            ;;
        "custom")
            custom_generate
            ;;
        "full")
            full_example
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            echo "❌ 未知选项: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主程序
main "$@"
