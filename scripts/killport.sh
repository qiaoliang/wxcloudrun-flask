#!/bin/bash

# killport.sh - 杀死使用指定端口范围的进程
# =============================================

# 设置端口范围
START_PORT=8000
END_PORT=9999

echo "正在查找使用端口 $START_PORT 到 $END_PORT 之间的进程..."

# 用于统计的变量
killed_count=0
total_found=0

# 使用 lsof 一次性查找所有端口范围内的进程
echo "正在扫描端口..."
pids=$(lsof -ti:$START_PORT-$END_PORT 2>/dev/null | sort -u)

if [ -z "$pids" ]; then
    echo "没有发现使用端口 $START_PORT 到 $END_PORT 的进程"
    exit 0
fi

# 逐个处理找到的进程
for pid in $pids; do
    # 检查进程是否仍然存在
    if ! kill -0 $pid 2>/dev/null; then
        continue
    fi
    
    total_found=$((total_found + 1))
    
    # 获取进程信息和使用的端口
    process_info=$(ps -p $pid -o pid,ppid,command --no-headers 2>/dev/null)
    # 只获取以8或9开头的4位数端口（8000-9999）
    ports=$(lsof -p $pid -i -n -P | grep -E "TCP.*LISTEN" | awk '{print $9}' | cut -d: -f2 | grep -E "^[89][0-9]{3}$" | sort -u | tr '\n' ' ')
    
    # 如果没有使用目标范围内的端口，跳过
    if [ -z "$ports" ]; then
        continue
    fi
    
    echo "发现进程使用端口 $ports:"
    echo "  $process_info"
    
    # 尝试优雅地终止进程
    echo "  正在终止进程 $pid..."
    kill $pid 2>/dev/null
    
    # 短暂等待
    sleep 0.5
    
    # 检查进程是否还在运行
    if kill -0 $pid 2>/dev/null; then
        # 如果还在运行，强制终止
        echo "  进程仍在运行，强制终止..."
        kill -9 $pid 2>/dev/null
        sleep 0.5
    fi
    
    # 再次检查
    if ! kill -0 $pid 2>/dev/null; then
        echo "  ✓ 进程 $pid 已被成功终止"
        killed_count=$((killed_count + 1))
    else
        echo "  ✗ 无法终止进程 $pid (可能需要更高权限)"
    fi
    
    echo ""
done

# 输出统计信息
echo "================================"
echo "任务完成！"
echo "发现的进程数: $total_found"
echo "成功终止的进程数: $killed_count"

if [ $total_found -eq 0 ]; then
    echo "没有发现使用端口 $START_PORT 到 $END_PORT 的进程"
fi