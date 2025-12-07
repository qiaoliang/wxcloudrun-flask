#!/bin/bash

# 过渡性入口脚本 - run.sh
# ========================

# 注意：这是一个过渡性的入口脚本，为了保持向后兼容性而存在。
# 真正的主程序已经移动到 src/main.py 中。

# 建议：
# - 开发时请直接使用 src/main.py
# - 构建生产环境时请使用 src/main.py
# - 此脚本仅用于临时过渡，未来可能会被移除

# 检查是否提供了所有必需参数
if [ $# -ne 3 ]; then
    echo "[ERROR] 请提供所有必需参数：环境类型 IP地址 端口号"
    echo "[INFO] 用法示例: ./run.sh unit 127.0.0.1 8080"
    echo "[INFO] 环境类型可选值: unit, func, uat, prod"
    exit 1
fi

# 验证环境类型参数是否有效
VALID_ENV_TYPES=("unit" "func" "uat" "prod")
if [[ ! " ${VALID_ENV_TYPES[@]} " =~ " $1 " ]]; then
    echo "[ERROR] 无效的环境类型 '$1'，请使用以下值之一: unit, func, uat, prod"
    exit 1
fi

# 验证IP地址格式（简单验证）
if [[ ! $2 =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "[ERROR] 无效的IP地址格式 '$2'，请使用正确的IPv4地址格式"
    exit 1
fi

# 验证端口号（简单验证：1-65535的数字）
if [[ ! $3 =~ ^[0-9]+$ ]] || [ "$3" -lt 1 ] || [ "$3" -gt 65535 ]; then
    echo "[ERROR] 无效的端口号 '$3'，请使用1-65535之间的数字"
    exit 1
fi

# 设置环境变量
export ENV_TYPE="$1"
export IP="$2"
export PORT="$3"
echo "[INFO] 设置环境变量 ENV_TYPE=$ENV_TYPE IP=$IP PORT=$PORT"

echo "[INFO] 使用过渡性入口脚本，真正的主程序在 src/main.py"

# 清理可能占用端口的进程
echo "[INFO] 正在清理端口 8000-9999 上的进程..."
if [[ -f "scripts/killport.sh" ]]; then
    ./scripts/killport.sh
else
    echo "[WARNING] 未找到 scripts/killport.sh，跳过端口清理"
fi

# 检查是否在虚拟环境中
if [[ "$VIRTUAL_ENV" != "" ]]; then
    # 已经在虚拟环境中，直接运行
    # 传递参数顺序：IP地址 端口号 (环境类型已通过环境变量传递)
    python src/main.py "$2" "$3"
else
    # 不在虚拟环境中，尝试激活本地虚拟环境
    if [[ -f "venv_py312/bin/activate" ]]; then
        source venv_py312/bin/activate
        # 传递参数顺序：IP地址 端口号 (环境类型已通过环境变量传递)
        python src/main.py "$2" "$3"
    else
        echo "[ERROR] 未检测到虚拟环境，请先激活虚拟环境或安装依赖"
        exit 1
    fi
fi