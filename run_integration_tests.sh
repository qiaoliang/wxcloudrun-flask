#!/bin/bash
# 运行集成测试的便捷脚本

set -e  # 遇到错误立即退出

# 颜要设置的环境变量
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# 检查虚拟环境
if [ ! -d "venv_py312" ]; then
    echo "错误: 虚拟环境 venv_py312 不存在"
    echo "请先运行: python3.12 -m venv venv_py312 && source venv_py312/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# 激活虚拟环境
source venv_py312/bin/activate

echo "========================================"
echo "运行微信与手机注册流程优化 - 集成测试"
echo "========================================"

# 运行所有集成测试
echo "运行所有集成测试..."
python -m pytest tests/integration/ -v

echo ""
echo "========================================"
echo "测试运行完成"
echo "========================================"