#!/usr/bin/env bash
# 本地开发启动脚本
# 这是一个便捷的包装器，调用 localrun.sh 来启动应用

echo "🚀 SafeGuard 本地开发环境启动"
echo "================================"

# 检查是否存在 localrun.sh
if [ ! -f "localrun.sh" ]; then
    echo "❌ 错误: 找不到 localrun.sh 脚本"
    exit 1
fi

# 执行 localrun.sh
echo "📦 正在启动应用..."
./localrun.sh

# 如果脚本异常退出，显示提示
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ 应用启动失败"
    echo "💡 提示: 检查日志或使用 ./localrun_complete.sh --reset-db 重置数据库"
fi