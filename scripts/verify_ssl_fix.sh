#!/bin/bash
# 验证Dockerfile修改

echo "=== 验证Dockerfile SSL修复修改 ==="
echo ""

cd "$(dirname "$0")/../"

echo "1. 检查Dockerfile中的CA证书更新配置..."
if grep -q "apt-get upgrade -y ca-certificates" Dockerfile; then
    echo "✅ CA证书升级配置已添加"
else
    echo "❌ CA证书升级配置未找到"
    exit 1
fi

echo ""
echo "2. 检查Dockerfile中的certifi升级配置..."
if grep -q "pip install --user --upgrade certifi" Dockerfile; then
    echo "✅ certifi升级配置已添加"
else
    echo "❌ certifi升级配置未找到"
    exit 1
fi

echo ""
echo "3. 检查构建脚本中的镜像名称..."
if grep -q "docker build -t s-prod" scripts/build-prod.sh; then
    echo "✅ 构建脚本镜像名称已更新为 s-prod"
else
    echo "❌ 构建脚本镜像名称未更新"
    exit 1
fi

echo ""
echo "4. 检查运行脚本中的容器名称..."
if grep -q "s-prod" scripts/run-prod.sh; then
    echo "✅ 运行脚本容器名称已更新为 s-prod"
else
    echo "❌ 运行脚本容器名称未更新"
    exit 1
fi

echo ""
echo "5. 显示修改后的Dockerfile关键部分..."
echo "================================"
grep -A 10 -B 2 "ca-certificates\|certifi" Dockerfile
echo "================================"

echo ""
echo "✅ 所有验证通过！Dockerfile SSL修复修改完成。"
echo ""
echo "下一步操作："
echo "1. 运行 './scripts/build-prod.sh' 构建生产镜像"
echo "2. 运行 './scripts/run-prod.sh' 启动生产容器"
echo "3. 或运行 './scripts/test_ssl_fix.sh' 进行SSL连接测试"