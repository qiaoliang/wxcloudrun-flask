#!/usr/bin/env bash
# 完整的启动脚本，自动处理数据库迁移和重置

# 激活虚拟环境
source venv_py312/bin/activate

# 进入src目录
cd src

# 解析命令行参数
RESET_DB=false
for arg in "$@"
do
    case $arg in
        --reset-db)
            RESET_DB=true
            ;;
        --help)
            echo "用法: $0 [--reset-db]"
            echo "选项:"
            echo "  --reset-db    删除现有数据库并重新创建"
            exit 0
            ;;
    esac
done

# 如果请求重置数据库
if [ "$RESET_DB" = true ]; then
    echo "正在删除现有数据库..."
    rm -f data/function.db
    echo "✅ 数据库已删除"
fi

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
    echo "✅ 发现现有迁移脚本，跳过生成"
fi

# 启动应用
echo "正在启动应用..."
ENV_TYPE=function python3.12 main.py 0.0.0.0 9999