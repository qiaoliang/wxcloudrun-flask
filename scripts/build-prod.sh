#!/bin/bash
# 构建 Production 环境的 Docker 镜像

set -e

echo "开始构建 Production 环境的 Docker 镜像..."

cd "$(dirname "$0")/../"

# 构建 Production 环境镜像（使用原始 Dockerfile）
docker build -t s-prod .

echo "Production 环境镜像构建完成！"
echo ""
echo "镜像名称: s-prod"
echo "要运行 Production 环境，请使用: ./scripts/run-prod.sh"