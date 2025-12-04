#!/bin/bash
# 运行 Production 环境的 Docker 容器

set -e

echo "启动 Production 环境的 Docker 容器..."

# 检查镜像是否存在
if [[ "$(docker images -q safeguard-prod-img 2> /dev/null)" == "" ]]; then
    echo "错误: 镜像 safeguard-prod-img 不存在，请先运行 build.sh"
    exit 1
fi

# 停止并删除之前的容器（如果有）
docker stop safeguard-prod 2>/dev/null || true
docker rm safeguard-prod 2>/dev/null || true

# 启动新的容器
docker run -d \
  --name safeguard-prod \
  -p 8080:8080 \
  -e ENV_TYPE=prod \
  -e SQLITE_DB_PATH=/app/data/prod.db \
  -e WX_APPID=your_wx_appid \
  -e WX_SECRET=your_wx_secret \
  -e TOKEN_SECRET=your_token_secret \
  safeguard-prod-img

echo "Production 环境容器已启动！"
echo "访问地址: http://localhost:8080"
echo "容器名称: safeguard-prod"
echo ""
echo "使用说明:"
echo "- 应用已启动并监听 8080 端口"
echo "- 访问 http://localhost:8080 查看应用状态（端口8080）"
echo "- 请确保已正确配置 WX_APPID, WX_SECRET, TOKEN_SECRET 环境变量"
echo ""
echo "要停止容器，请运行: ./scripts/stop-all.sh"
