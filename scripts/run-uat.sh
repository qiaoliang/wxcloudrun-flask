#!/bin/bash
# 运行 UAT 环境的 Docker 容器

set -e

echo "启动 UAT 环境的 Docker 容器..."

# 检查镜像是否存在
if [[ "$(docker images -q safeguard-uat-img 2> /dev/null)" == "" ]]; then
    echo "错误: 镜像 safeguard-uat-img 不存在，请先运行 ./scripts/build-uat.sh"
    exit 1
fi

# 停止并删除之前的容器（如果有）
docker stop safeguard-uat 2>/dev/null || true
docker rm safeguard-uat 2>/dev/null || true

# 启动新的容器
echo "正在启动容器..."
CONTAINER_ID=$(docker run -d \
  --name safeguard-uat \
  -p 9091:8080 \
  -e ENV_TYPE=uat \
  -e WX_APPID=test_appid \
  -e WX_SECRET=test_secret \
  -e TOKEN_SECRET=your_uat_jwt_secret_replace_with_strong_secret \
  safeguard-uat-img)

echo "UAT 环境容器已启动！"
echo "容器ID: $CONTAINER_ID"
echo "访问地址: http://localhost:9091"
echo "容器名称: safeguard-uat"
echo ""

# 等待容器启动
echo "等待容器启动..."
sleep 3

# 检查容器状态
CONTAINER_STATUS=$(docker inspect --format='{{.State.Status}}' safeguard-uat)
echo "容器状态: $CONTAINER_STATUS"

if [[ "$CONTAINER_STATUS" != "running" ]]; then
    echo "⚠️  容器启动失败，显示错误日志："
    echo "================================"
    docker logs safeguard-uat
    echo "================================"
    exit 1
fi

# 显示启动日志
echo "✅ 容器运行正常，显示启动日志："
echo "================================"
# 显示最近的日志，限制行数避免输出过多
docker logs --tail 20 safeguard-uat
echo "================================"

echo ""
echo "使用说明:"
echo "- 应用已启动并监听 9091 端口"
echo "- 微信API使用Mock服务，短信服务使用真实服务"
echo "- 访问 http://localhost:9091 查看应用状态（端口9091）"
echo "- 访问 http://localhost:9091/api/count 查看计数器 API"
echo "- 访问 http://localhost:9091/api/login 进行微信登录测试"
echo "- 短信验证码将发送到真实手机号"
echo ""
echo "要查看实时日志，请运行: docker logs -f safeguard-uat"
echo "要停止容器，请运行: ./scripts/stop-all.sh"