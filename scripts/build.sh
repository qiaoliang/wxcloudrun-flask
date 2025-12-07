#!/bin/bash
# 构建所有 Docker 镜像（完整构建）

set -e

echo "开始构建所有 Docker 镜像..."

# 运行所有单独的构建脚本
./scripts/build-function.sh
./scripts/build-uat.sh
./scripts/build-prod.sh

echo ""
echo "所有镜像构建完成！"
echo ""
echo "构建的镜像:"
echo "- safeguard-base: 基础镜像（包含 Python 依赖）"
echo "- safeguard-function-img: Function 环境镜像"
echo "- safeguard-uat-img: UAT 环境镜像"
echo "- s-prod: Production 环境镜像"
echo ""
echo "要运行环境，请使用相应的脚本："
echo "  ./scripts/run-function.sh  # 运行功能测试环境"
echo "  ./scripts/run-uat.sh      # 运行UAT环境"
echo "  ./scripts/run-prod.sh    # 运行生产环境"
echo ""
echo "要查看容器状态，请运行: ./scripts/status.sh"