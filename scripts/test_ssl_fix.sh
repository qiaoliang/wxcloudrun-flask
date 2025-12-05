#!/bin/bash
# 测试SSL证书修复效果

set -e

echo "=== SSL证书修复测试脚本 ==="
echo ""

# 构建测试镜像
echo "1. 构建测试镜像..."
cd "$(dirname "$0")/../"
docker build -t ssl-test-img .

echo ""
echo "2. 启动测试容器..."

# 停止并删除之前的测试容器（如果有）
docker stop ssl-test 2>/dev/null || true
docker rm ssl-test 2>/dev/null || true

# 启动测试容器
CONTAINER_ID=$(docker run -d \
  --name ssl-test \
  -e ENV_TYPE=prod \
  ssl-test-img)

echo "测试容器已启动，容器ID: $CONTAINER_ID"

# 等待容器启动
echo "等待容器启动..."
sleep 5

# 检查容器状态
CONTAINER_STATUS=$(docker inspect --format='{{.State.Status}}' ssl-test)
echo "容器状态: $CONTAINER_STATUS"

if [[ "$CONTAINER_STATUS" != "running" ]]; then
    echo "⚠️  容器启动失败，显示错误日志："
    echo "================================"
    docker logs ssl-test
    echo "================================"
    exit 1
fi

echo ""
echo "3. 测试SSL证书连接..."

# 在容器内测试SSL连接
docker exec ssl-test python3 -c "
import requests
import sys

print('测试微信API SSL连接...')
try:
    response = requests.get(
        'https://api.weixin.qq.com/sns/jscode2session?appid=test&secret=test&js_code=test&grant_type=authorization_code',
        timeout=10,
        verify=True
    )
    print('✅ SSL连接成功！')
    print(f'状态码: {response.status_code}')
    print(f'响应: {response.text[:100]}...')
except Exception as e:
    print(f'❌ SSL连接失败: {str(e)}')
    sys.exit(1)
"

echo ""
echo "4. 检查certifi版本..."
docker exec ssl-test python3 -c "
import certifi
import requests
print(f'certifi版本: {certifi.__version__}')
print(f'certifi路径: {certifi.where()}')
print(f'requests版本: {requests.__version__}')
"

echo ""
echo "5. 清理测试容器..."
docker stop ssl-test
docker rm ssl-test

echo ""
echo "✅ SSL证书修复测试完成！"