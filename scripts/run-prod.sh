#!/bin/bash
# 运行 Production 环境的 Docker 容器

set -e

echo "启动 Production 环境的 Docker 容器..."

# 检查镜像是否存在
if [[ "$(docker images -q safeguard-prod-img 2> /dev/null)" == "" ]]; then
    echo "错误: 镜像 safeguard-prod-img 不存在，请先运行 build-prod.sh"
    exit 1
fi

# 停止并删除之前的容器（如果有）
docker stop s-prod 2>/dev/null || true
docker rm s-prod 2>/dev/null || true

# 检查并停止其他占用8080端口的容器
echo "检查8080端口占用情况..."
OCCUPYING_CONTAINER=$(docker ps -q --filter "publish=8080")
if [ ! -z "$OCCUPYING_CONTAINER" ]; then
    echo "发现占用8080端口的容器，正在停止..."
    docker stop $OCCUPYING_CONTAINER
    echo "已停止占用8080端口的容器"
else
    echo "8080端口未被占用"
fi

# 启动新的容器
echo "正在启动容器..."
CONTAINER_ID=$(docker run -d \
  --name s-prod \
  -p 8080:8080 \
  -e ENV_TYPE=prod \
  -e WX_APPID=your_wx_appid \
  -e WX_SECRET=your_wx_secret \
  -e TOKEN_SECRET=your_token_secret \
  safeguard-prod-img)

echo "Production 环境容器已启动！"
echo "容器ID: $CONTAINER_ID"
echo "访问地址: http://localhost:8080"
echo "容器名称: s-prod"
echo ""

# 等待容器启动
echo "等待容器启动..."
sleep 3

# 检查容器状态
CONTAINER_STATUS=$(docker inspect --format='{{.State.Status}}' s-prod)
echo "容器状态: $CONTAINER_STATUS"

if [[ "$CONTAINER_STATUS" != "running" ]]; then
    echo "⚠️  容器启动失败，显示错误日志："
    echo "================================"
    docker logs s-prod
    echo "================================"
    exit 1
fi

# 显示启动日志
echo "✅ 容器运行正常，显示启动日志："
echo "================================"
# 显示最近的日志，限制行数避免输出过多
docker logs --tail 20 s-prod
echo "================================"

echo ""
echo "使用说明:"
echo "- 应用已启动并监听 8080 端口"
echo "- 访问 http://localhost:8080 查看应用状态（端口8080）"
echo "- 请确保已正确配置 WX_APPID, WX_SECRET, TOKEN_SECRET 环境变量"
echo ""
echo "要查看实时日志，请运行: docker logs -f s-prod"
echo "要停止容器，请运行: ./scripts/stop-all.sh"
