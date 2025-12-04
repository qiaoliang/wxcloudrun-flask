#!/bin/bash
# 查看安全守护 Docker 容器状态

echo "安全守护容器状态:"
echo "=================="

# 查找所有相关的容器
containers=$(docker ps -a --filter "name=safeguard-" --format "table {{.Names}}	{{.Status}}	{{.Ports}}")

if [ -n "$containers" ]; then
    echo "$containers"
else
    echo "没有找到相关的容器"
fi

echo ""
echo "端口映射信息:"
echo "=============="
echo "Function 环境: 9090 -> 8080" 
echo "Production 环境: 8080 -> 8080"
echo ""

echo "镜像状态:"
echo "=========="
if [ -n "$(docker images -q safeguard-function-img 2>/dev/null)" ]; then
    docker images safeguard-function-img
else
    echo "镜像 safeguard-function-img 不存在"
fi
if [ -n "$(docker images -q safeguard-prod-img 2>/dev/null)" ]; then
    docker images safeguard-prod-img
else
    echo "镜像 safeguard-prod-img 不存在"
fi
