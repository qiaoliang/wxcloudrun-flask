#!/bin/bash
# 运行 Function 环境的 Docker 容器

set -e

echo "启动 Function 环境的 Docker 容器..."

# 检查镜像是否存在
if [[ "$(docker images -q safeguard-function-img 2> /dev/null)" == "" ]]; then
    echo "错误: 镜像 safeguard-function-img 不存在，请先运行 build.sh"
    exit 1
fi

# 停止并删除之前的容器（如果有）
docker stop s-function 2>/dev/null || true
docker rm s-function 2>/dev/null || true

# 启动新的容器
echo "正在启动容器..."
CONTAINER_ID=$(docker run -d \
  --name s-function \
  -p 9090:8080 \
  -e ENV_TYPE=function \
  safeguard-function-img)

echo "Function 环境容器已启动！"
echo "容器ID: $CONTAINER_ID"
echo "访问地址: http://localhost:9090"
echo "容器名称: s-function"
echo ""

# 等待容器启动
echo "等待容器启动..."
sleep 3

# 检查容器状态
CONTAINER_STATUS=$(docker inspect --format='{{.State.Status}}' s-function)
echo "容器状态: $CONTAINER_STATUS"

if [[ "$CONTAINER_STATUS" != "running" ]]; then
    echo "⚠️  容器启动失败，显示错误日志："
    echo "================================"
    docker logs s-function
    echo "================================"
    exit 1
fi

# 显示启动日志
echo "✅ 容器运行正常，显示启动日志："
echo "================================"
# 显示最近的日志，限制行数避免输出过多
docker logs --tail 20 s-function
echo "================================"

echo ""
echo "使用说明:"
echo "- 应用已启动并监听 9090 端口"
echo "- 访问 http://localhost:9090 查看应用状态（端口9090）"
echo "- 访问 http://localhost:9090/api/count 查看计数器 API"
echo "- 访问 http://localhost:9090/api/login 进行微信登录测试"
echo ""
echo "要查看实时日志，请运行: docker logs -f safeguard-function"
echo "要停止容器，请运行: ./scripts/stop-all.sh"