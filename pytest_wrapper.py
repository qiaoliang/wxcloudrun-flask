#!/usr/bin/env python
"""pytest wrapper to ensure proper environment setup"""
import os
import sys

# 确保src目录在Python路径中
src_path = os.path.join(os.path.dirname(__file__), 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# 设置PYTHONPATH环境变量
os.environ['PYTHONPATH'] = f"{src_path}:{os.environ.get('PYTHONPATH', '')}"

# 运行pytest
import pytest
sys.exit(pytest.main(sys.argv[1:]))