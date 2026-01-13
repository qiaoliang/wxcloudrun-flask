#!/usr/bin/env bash
# 改进的启动脚本
# 注意：数据库迁移已由 run.py 的 main() 函数自动处理

kill $(lsof -ti:8888-9999) 2>/dev/null || true

# 激活虚拟环境
source venv_py312/bin/activate

# 进入src目录
cd src

# 获取端口配置（优先使用环境变量，否则根据环境类型使用默认值）
if [ -z "$EXPOSE_PORT" ]; then
    # 如果未设置 EXPOSE_PORT，根据环境类型设置默认端口
    if [ "$ENV_TYPE" = "function" ] || [ "$ENV_TYPE" = "unit" ]; then
        PORT=9999
    else
        PORT=8080
    fi
else
    PORT=$EXPOSE_PORT
fi

# 导出端口环境变量供 run.py 使用
export EXPOSE_PORT=$PORT

# 启动应用
echo "🌟 正在启动 SafeGuard 应用..."
echo "📍 访问地址: http://localhost:${PORT}"
echo "📍 环境配置: http://localhost:${PORT}/api/env"
echo "⏳ 等待服务启动..."
echo ""
ENV_TYPE=function python3.12 run.py
