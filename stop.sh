#!/usr/bin/env bash
# 停止 SafeGuard 后端服务

cd "$(dirname "$0")"

# 检查是否有 PID 文件
if [ -f "src/logs/server.pid" ]; then
    PID=$(cat src/logs/server.pid)
    
    # 检查进程是否还在运行
    if ps -p $PID > /dev/null; then
        echo "🛑 正在停止服务 (PID: $PID)..."
        kill $PID
        
        # 等待进程结束
        for i in {1..10}; do
            if ! ps -p $PID > /dev/null; then
                echo "✅ 服务已停止"
                rm -f src/logs/server.pid
                exit 0
            fi
            sleep 1
        done
        
        # 如果进程还在运行，强制杀死
        echo "⚠️  服务未响应，强制停止..."
        kill -9 $PID
        rm -f src/logs/server.pid
        echo "✅ 服务已强制停止"
    else
        echo "⚠️  进程不存在，清理 PID 文件"
        rm -f src/logs/server.pid
    fi
else
    # 如果没有 PID 文件，尝试根据端口查找进程
    PORT=${1:-9999}
    PID=$(lsof -ti:${PORT} 2>/dev/null)
    
    if [ -n "$PID" ]; then
        echo "🛑 正在停止端口 ${PORT} 上的服务 (PID: $PID)..."
        kill $PID
        echo "✅ 服务已停止"
    else
        echo "ℹ️  没有找到运行中的服务"
    fi
fi