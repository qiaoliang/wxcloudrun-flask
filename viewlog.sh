#!/usr/bin/env bash
# 查看 SafeGuard 后端服务日志

cd "$(dirname "$0")/src/logs"

# 如果没有参数，显示最新的日志文件
if [ $# -eq 0 ]; then
    LATEST_LOG=$(ls -t server_*.log 2>/dev/null | head -1)
    
    if [ -z "$LATEST_LOG" ]; then
        echo "❌ 没有找到日志文件"
        exit 1
    fi
    
    echo "📊 查看最新日志: ${LATEST_LOG}"
    echo "🔄 实时跟踪日志 (Ctrl+C 退出)"
    echo ""
    tail -f "${LATEST_LOG}"
else
    # 如果有参数，使用 tail 命令
    tail -f "$@"
fi