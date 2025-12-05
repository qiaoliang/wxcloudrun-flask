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
docker stop safeguard-function 2>/dev/null || true
docker rm safeguard-function 2>/dev/null || true

# 启动新的容器
docker run -d \
  --name safeguard-function \
  -p 9090:8080 \
  -e ENV_TYPE=function \
  -e WX_APPID=test_appid \
  -e WX_SECRET=test_secret \
  -e TOKEN_SECRET=42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f \
  safeguard-function-img

echo "Function 环境容器已启动！"
echo "访问地址: http://localhost:9090"
echo "容器名称: safeguard-function"
echo ""
echo "使用说明:"
echo "- 应用已启动并监听 9090 端口"
echo "- 访问 http://localhost:9090 查看应用状态（端口9090）"
echo "- 访问 http://localhost:9090/api/count 查看计数器 API"
echo "- 访问 http://localhost:9090/api/login 进行微信登录测试"
echo ""
echo "要停止容器，请运行: ./scripts/stop-all.sh"