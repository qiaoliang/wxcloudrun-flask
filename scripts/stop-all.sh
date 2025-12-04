#!/bin/bash
# 停止并删除所有相关的 Docker 容器

echo "停止所有安全守护容器..."

docker stop safeguard-function 2>/dev/null || true
docker stop safeguard-prod 2>/dev/null || true

docker rm safeguard-function 2>/dev/null || true
docker rm safeguard-prod 2>/dev/null || true

echo "所有容器已停止并删除"
echo ""
echo "使用说明:"
echo "- 要重新启动应用，请运行相应的启动脚本"
echo "  ./scripts/run-function.sh  # 重新运行功能测试环境"
echo "  ./scripts/run-prod.sh    # 重新运行生产环境"
echo ""
echo "要构建新镜像（如代码有更新），请运行: ./scripts/build.sh"
echo ""
echo "使用说明:"
echo "- 要重新启动应用，请运行相应的启动脚本"
echo "  ./scripts/run-function.sh  # 重新运行功能测试环境"
echo "  ./scripts/run-prod.sh    # 重新运行生产环境"
echo "  ./scripts/run-unit.sh    # 重新运行单元测试环境"
echo ""
echo "要构建新镜像（如代码有更新），请运行: ./scripts/build.sh"