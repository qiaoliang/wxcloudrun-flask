#!/bin/bash

# 手动测试脚本 - 运行集成测试，使用真实微信凭证
# 注意：此脚本依赖环境变量设置，不自动启动Docker容器

set -e  # 遇到错误时退出

echo "=== 手动集成测试脚本 ==="
echo "此脚本将运行集成测试，使用真实微信API凭证"
echo ""

# 加载环境变量配置文件
ENV_FILE=".env.manual"
if [ -f "$ENV_FILE" ]; then
    echo "加载环境变量配置文件: $ENV_FILE"
    export $(grep -v '^#' "$ENV_FILE" | xargs)
else
    echo "警告: 未找到环境变量配置文件 $ENV_FILE"
    echo "请创建配置文件，格式如下："
    echo "  WX_APPID=your_real_appid"
    echo "  WX_SECRET=your_real_secret"
    echo "  TOKEN_SECRET=your_real_token_secret"
    echo "  MYSQL_PASSWORD=your_mysql_password"
    echo "  MYSQL_USERNAME=root"
    echo "  MYSQL_ADDRESS=127.0.0.1:3306"
    exit 1
fi

# 检查Python虚拟环境
if [ ! -f "venv_py312/bin/activate" ]; then
    echo "错误: 未找到Python 3.12虚拟环境 (venv_py312)"
    exit 1
fi

echo "✓ 找到Python 3.12虚拟环境"

# 检查是否设置了真实微信API凭证
if [ -z "$WX_APPID" ] || [ -z "$WX_SECRET" ] || [[ "$WX_APPID" == *"test"* ]] || [[ "$WX_SECRET" == *"test"* ]]; then
    echo "错误: 未设置真实的微信API凭证 (WX_APPID 或 WX_SECRET)"
    echo "请检查 $ENV_FILE 文件中的以下变量:"
    echo "  WX_APPID=your_real_appid"
    echo "  WX_SECRET=your_real_secret"
    echo ""
    echo "提示: 如果使用测试值（包含'test'），微信API测试将被跳过"
    exit 1
else
    echo "✓ 检测到微信API凭证"
fi

# 激活虚拟环境
source venv_py312/bin/activate

# 设置其他环境变量（如果未设置）
export USE_SQLITE_FOR_TESTING="${USE_SQLITE_FOR_TESTING:-false}"
export FLASK_ENV="${FLASK_ENV:-production}"

echo "✓ 设置环境变量"

# 检查Docker服务是否运行
if ! docker ps >/dev/null 2>&1; then
    echo "警告: Docker服务未运行，集成测试可能失败"
else
    # 检查容器是否正在运行
    if docker ps | grep -q "py-safeclockin-dev" && docker ps | grep -q "mysql-db-dev"; then
        echo "✓ 检测到Docker容器正在运行"
    else
        echo "警告: 未检测到Docker容器，集成测试可能失败"
        echo "如果需要，请运行: docker-compose -f docker-compose.dev.yml up -d"
    fi
fi

# 等待服务完全启动
echo "等待服务响应..."
timeout=30
count=0
while [ $count -lt $timeout ]; do
    if curl -s http://localhost:8080/ >/dev/null 2>&1; then
        echo "✓ 服务已就绪"
        break
    fi
    sleep 2
    ((count += 2))
done

if [ $count -ge $timeout ]; then
    echo "警告: 服务未在预期时间内响应，测试可能失败"
fi

# 运行集成测试 - 不跳过任何测试用例
echo "=== 开始运行集成测试 ==="
echo "测试将使用真实的微信API凭证"

# 设置一个标志，让测试知道这是手动运行模式
export MANUAL_TEST_MODE="true"

# 运行所有集成测试
python -m pytest tests/integration_test_counter.py tests/integration_test_login.py -v -s --tb=short

echo "=== 测试完成 ==="

# 检查测试结果
if [ $? -eq 0 ]; then
    echo "✓ 所有集成测试通过！"
else
    echo "✗ 部分测试失败"
    exit 1
fi