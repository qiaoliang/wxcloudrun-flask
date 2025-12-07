#!/bin/bash
# 查看容器日志的辅助脚本

set -e

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项] [容器名称]"
    echo ""
    echo "选项:"
    echo "  -f, --follow     实时跟踪日志输出"
    echo "  -t, --tail N     显示最后N行日志（默认20）"
    echo "  -h, --help       显示此帮助信息"
    echo ""
    echo "容器名称:"
    echo "  s-function         Function环境容器"
    echo "  s-uat              UAT环境容器"
    echo "  s-prod             生产环境容器"
    echo ""
    echo "示例:"
    echo "  $0                    # 显示所有容器的最近20行日志"
    echo "  $0 -f s-uat          # 实时跟踪UAT容器日志"
    echo "  $0 -t 50 s-prod      # 显示生产容器最近50行日志"
}

# 默认参数
FOLLOW=false
TAIL_LINES=20
CONTAINER_NAME=""

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--follow)
            FOLLOW=true
            shift
            ;;
        -t|--tail)
            TAIL_LINES="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        s-function|s-uat|s-prod)
            CONTAINER_NAME="$1"
            shift
            ;;
        *)
            echo "未知参数: $1"
            show_help
            exit 1
            ;;
    esac
done

# 构建docker logs命令
build_docker_logs_cmd() {
    local container=$1
    local cmd="docker logs"
    
    if [[ "$FOLLOW" == "true" ]]; then
        cmd="$cmd -f"
    else
        cmd="$cmd --tail $TAIL_LINES"
    fi
    
    cmd="$cmd $container"
    echo "$cmd"
}

# 检查容器是否存在
check_container_exists() {
    local container=$1
    if ! docker ps -a --format '{{.Names}}' | grep -q "^${container}$"; then
        echo "❌ 容器 $container 不存在"
        return 1
    fi
    return 0
}

# 显示容器日志
show_container_logs() {
    local container=$1
    local container_status=$(docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null || echo "unknown")
    
    echo "================================"
    echo "容器: $container (状态: $container_status)"
    echo "================================"
    
    if [[ "$container_status" != "running" && "$FOLLOW" != "true" ]]; then
        echo "⚠️  容器未运行，显示历史日志："
    fi
    
    local cmd=$(build_docker_logs_cmd "$container")
    eval "$cmd"
    echo ""
}

# 主逻辑
if [[ -z "$CONTAINER_NAME" ]]; then
    # 显示所有容器的日志
    echo "显示所有容器日志..."
    echo ""
    
    for container in s-function s-uat s-prod; do
        if check_container_exists "$container"; then
            show_container_logs "$container"
        fi
    done
else
    # 显示指定容器的日志
    if check_container_exists "$CONTAINER_NAME"; then
        show_container_logs "$CONTAINER_NAME"
    else
        echo "❌ 容器 $CONTAINER_NAME 不存在"
        echo ""
        echo "可用的容器："
        docker ps -a --format '{{.Names}}' | grep safeguard- || echo "无safeguard容器"
        exit 1
    fi
fi