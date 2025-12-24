#!/usr/bin/env bash
# 改进的启动脚本，自动处理数据库迁移

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

# 启动应用
echo "🌟 正在启动 SafeGuard 应用..."
echo "📍 访问地址: http://localhost:9999"
echo "📍 环境配置: http://localhost:9999/api/env"
echo "⏳ 等待服务启动..."
echo ""
ENV_TYPE=function python3.12 run.py 0.0.0.0 9999