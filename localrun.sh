#!/usr/bin/env bash
# 改进的启动脚本，自动处理数据库迁移

kill $(lsof -ti:8888-9999) 2>/dev/null || true

# 激活虚拟环境
source venv_py312/bin/activate

# 进入src目录
cd src

# 检查是否存在迁移脚本
if [ ! "$(ls -A alembic/versions/*.py 2>/dev/null)" ]; then
    echo "没有找到迁移脚本，正在生成..."
    
    # 生成初始迁移脚本
    alembic revision --autogenerate -m "init_db"
    
    if [ $? -eq 0 ]; then
        echo "✅ 迁移脚本生成成功"
    else
        echo "❌ 迁移脚本生成失败"
        exit 1
    fi
else
    echo "✅ 发现现有迁移脚本"
fi

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
