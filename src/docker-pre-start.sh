#!/bin/bash
# Docker 数据库迁移脚本

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

# 执行数据库迁移
echo "正在执行数据库迁移..."
alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✅ 数据库迁移成功"
else
    echo "❌ 数据库迁移失败"
    exit 1
fi