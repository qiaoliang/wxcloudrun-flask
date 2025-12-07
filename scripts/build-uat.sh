#!/bin/bash
# 构建 UAT 环境的 Docker 镜像

set -e

echo "开始构建 UAT 环境的 Docker 镜像..."

cd "$(dirname "$0")/../"

# 检查基础镜像是否存在，如果不存在则先构建
if [[ "$(docker images -q safeguard-base 2> /dev/null)" == "" ]]; then
    echo "基础镜像不存在，正在构建基础镜像..."
    docker build -f dockerfiles/Dockerfile.base -t safeguard-base .
fi

# 构建 UAT 环境镜像
docker build -f dockerfiles/Dockerfile.uat -t safeguard-uat-img .

echo "UAT 环境镜像构建完成！"
echo ""
echo "镜像名称: safeguard-uat-img"
echo "要运行 UAT 环境，请使用: ./scripts/run-uat.sh"