#!/bin/bash
# 停止并删除所有相关的 Docker 容器

echo "正在停止所有安全守护容器..."

# 检查并停止容器
for container in safeguard-function safeguard-uat safeguard-prod; do
    if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        echo "停止容器: $container"
        docker stop "$container"
    else
        echo "容器 $container 未运行"
    fi
done

echo ""
echo "正在删除容器..."

# 删除容器
for container in safeguard-function safeguard-uat safeguard-prod; do
    if docker ps -a --format '{{.Names}}' | grep -q "^${container}$"; then
        echo "删除容器: $container"
        docker rm "$container"
    else
        echo "容器 $container 不存在"
    fi
done

echo ""
echo "✅ 所有容器已停止并删除"
echo ""
echo "使用说明:"
echo "- 要重新启动应用，请运行相应的启动脚本"
echo "  ./scripts/run-function.sh  # 重新运行功能测试环境"
echo "  ./scripts/run-uat.sh      # 重新运行UAT环境"
echo "  ./scripts/run-prod.sh    # 重新运行生产环境"
echo ""
echo "要查看容器日志，请运行:"
echo "  ./scripts/logs.sh          # 查看所有容器日志"
echo "  ./scripts/logs.sh -f       # 实时跟踪所有容器日志"
echo "  ./scripts/logs.sh safeguard-uat  # 查看UAT容器日志"
echo ""
echo "要构建新镜像（如代码有更新），请运行相应的构建脚本"
echo "  ./scripts/build-function.sh  # 构建功能测试环境"
echo "  ./scripts/build-uat.sh      # 构建UAT环境"
echo "  ./scripts/build-prod.sh    # 构建生产环境"