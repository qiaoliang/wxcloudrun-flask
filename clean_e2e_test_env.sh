#!/bin/bash
# 清理E2E测试环境脚本
# 删除数据库文件和迁移文件，确保每次测试都从干净的环境开始

echo "=== 清理E2E测试环境 ==="

# 获取当前脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 激活虚拟环境
source "${SCRIPT_DIR}/venv_py312/bin/activate"

# 设置环境变量
export ENV_TYPE=function

# 进入src目录
cd "${SCRIPT_DIR}/src"

# 删除数据库文件
if [ -f "data/function.db" ]; then
    echo "删除数据库文件: data/function.db"
    rm -f "data/function.db"
else
    echo "数据库文件不存在: data/function.db"
fi

# 删除迁移文件（保留__pycache__目录但删除.py迁移文件）
if [ -d "alembic/versions" ]; then
    echo "删除迁移文件..."
    find "alembic/versions" -name "*.py" -not -name "__init__.py" -type f -delete
    echo "迁移文件已删除"
else
    echo "迁移目录不存在: alembic/versions"
fi

# 重新生成迁移文件
echo "重新生成数据库迁移..."
alembic revision --autogenerate -m "init_db"

if [ $? -eq 0 ]; then
    echo "✅ 迁移文件生成成功"
else
    echo "❌ 迁移文件生成失败"
    exit 1
fi

# 执行数据库升级
echo "执行数据库升级..."
alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✅ 数据库升级成功"
else
    echo "❌ 数据库升级失败"
    exit 1
fi

echo "=== E2E测试环境清理完成 ==="