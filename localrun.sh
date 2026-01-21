#!/usr/bin/env bash
# 改进的启动脚本
# 注意：数据库迁移已由 run.py 的 main() 函数自动处理

# 进入脚本所在目录
cd "$(dirname "$0")"

kill $(lsof -ti:8888-9999) 2>/dev/null || true

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="${SCRIPT_DIR}/venv_py312/bin/python3.12"

# 检查虚拟环境是否存在
if [ ! -f "$VENV_PYTHON" ]; then
    echo "❌ 虚拟环境不存在: $VENV_PYTHON"
    echo "请先创建虚拟环境: python3.12 -m venv venv_py312"
    exit 1
fi

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

# 确保日志目录存在
mkdir -p logs

# 获取当前时间戳用于日志文件名
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="logs/server_${TIMESTAMP}.log"

# 启动应用（后台运行并输出到日志文件）
echo "🌟 正在启动 SafeGuard 应用..."
echo "📍 访问地址: http://localhost:${PORT}"
echo "📍 环境配置: http://localhost:${PORT}/api/env"
echo "📝 日志文件: $(pwd)/${LOG_FILE}"
echo "⏳ 等待服务启动..."
echo ""

# 使用虚拟环境的 Python 解释器在后台运行，将标准输出和标准错误都重定向到日志文件
nohup env ENV_TYPE=function "$VENV_PYTHON" -u run.py > "${LOG_FILE}" 2>&1 &

# 保存进程ID
echo $! > logs/server.pid

# 等待几秒让服务启动
sleep 3

# 检查服务是否启动成功
if ps -p $(cat logs/server.pid) > /dev/null; then
    echo "✅ 服务启动成功！"
    echo "📊 查看实时日志: tail -f ${LOG_FILE}"
    echo "🛑 停止服务: kill \$(cat logs/server.pid)"
else
    echo "❌ 服务启动失败，请查看日志文件：${LOG_FILE}"
    tail -n 20 "${LOG_FILE}"
fi
