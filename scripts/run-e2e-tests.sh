#!/bin/bash
# 运行E2E测试脚本

set -e

echo "=== 运行E2E测试 ==="

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "错误: Docker未运行，请先启动Docker"
    exit 1
fi

# 检查UAT镜像是否存在
if ! docker images | grep -q "safeguard-uat-img"; then
    echo "UAT镜像不存在，正在构建..."
    ./scripts/build-uat.sh
fi

# 运行测试
echo "正在运行E2E测试..."
cd backend
pytest tests/e2e/ -v --tb=short

echo "=== E2E测试完成 ==="