#!/bin/bash
# 运行E2E测试脚本

set -e

echo "=== 运行E2E测试 ==="

# 获取当前脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 激活虚拟环境
source "${PROJECT_DIR}/venv_py312/bin/activate"

# 清理E2E测试环境（删除数据库文件和迁移文件）
echo "清理E2E测试环境..."
"${PROJECT_DIR}/clean_e2e_test_env.sh"

# 运行测试
echo "正在运行E2E测试..."
cd "${PROJECT_DIR}/src"
ENV_TYPE=function python -m pytest "${PROJECT_DIR}/tests/e2e/" -v --tb=short

echo "=== E2E测试完成 ==="