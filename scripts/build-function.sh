#!/bin/bash
# 构建 Function 环境的 Docker 镜像

set -e
echo "========= START ======================"
echo "开始构建 Function 环境的 Docker 镜像..."

cd "$(dirname "$0")/../"

# 构建镜像，使用统一Dockerfile和function目标
docker build \
  --target function \
  --build-arg ENV_TYPE=function \
  --build-arg EXPOSE_PORT=9999 \
  -t safeguard-function-img \
  .

echo "Function 环境镜像构建完成！"
echo ""
echo "镜像名称: safeguard-function-img"
echo "要运行 Function 环境，请使用: ./scripts/run-function.sh"
