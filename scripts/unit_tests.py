#!/usr/bin/env python
"""
单元测试脚本：专门运行单元测试，不包含 Docker 集成测试
"""

import sys
import subprocess
import argparse
import os
from pathlib import Path

# 添加脚本目录到路径，以便导入load_env
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from load_env import load_env_file, get_env_with_defaults


def run_unit_tests(test_path=None, with_coverage=False, html_report=False, min_coverage=80):
    """
    Run unit tests with optional coverage.
    
    Args:
        test_path (str): Path to specific test file or directory (excluding integration tests)
        with_coverage (bool): Whether to run with coverage
        html_report (bool): Whether to generate HTML coverage report
        min_coverage (int): Minimum required coverage percentage
    """
    # 加载环境变量配置
    load_env_file(".env.unit")  # 单元测试专用环境变量文件
    
    # 设置默认环境变量
    default_env = {
        'USE_SQLITE_FOR_TESTING': 'true',  # 确保使用SQLite进行单元测试
        'FLASK_ENV': 'testing',
        'WX_APPID': 'test_appid',  # 默认测试值，会导致跳过微信API测试
        'WX_SECRET': 'test_secret'  # 默认测试值，会导致跳过微信API测试
    }
    
    # 获取环境变量，未设置的使用默认值
    env_vars = get_env_with_defaults(default_env)
    
    # 创建环境变量副本并更新
    env = os.environ.copy()
    env.update(env_vars)
    
    cmd = [sys.executable, '-m', 'pytest']
    
    # 排除 Docker 集成测试，只运行单元测试
    if test_path:
        cmd.append(test_path)
    else:
        cmd.append('tests/')
    
    # 排除 Docker 集成测试文件
    cmd.extend(['--ignore=tests/integration_test_docker.py'])
    
    if with_coverage:
        cmd.extend([
            '--cov=wxcloudrun',
            f'--cov-fail-under={min_coverage}'
        ])
        
        if html_report:
            cmd.extend(['--cov-report=html', '--cov-report=term-missing'])
        else:
            cmd.extend(['--cov-report=term-missing'])
    
    # Add verbose output by default
    cmd.append('-v')
    
    print(f"Running unit tests command: {' '.join(cmd)}")
    result = subprocess.run(cmd, env=env)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description='Unit test runner for Flask application')
    parser.add_argument('test_path', nargs='?', help='Specific test file or directory to run (excluding integration tests)')
    parser.add_argument('--coverage', action='store_true', help='Run tests with coverage')
    parser.add_argument('--html-report', action='store_true', help='Generate HTML coverage report')
    parser.add_argument('--min-coverage', type=int, default=80, help='Minimum required coverage percentage')
    
    args = parser.parse_args()
    
    return run_unit_tests(
        test_path=args.test_path,
        with_coverage=args.coverage,
        html_report=args.html_report,
        min_coverage=args.min_coverage
    )


if __name__ == '__main__':
    sys.exit(main())