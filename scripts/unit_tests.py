#!/usr/bin/env python
"""
单元测试脚本：专门运行单元测试，不包含 Docker 集成测试
"""

import sys
import subprocess
import argparse
import os
from pathlib import Path
from dotenv import load_dotenv


def run_unit_tests(test_path=None, with_coverage=False, html_report=False, min_coverage=80):
    """
    Run unit tests with optional coverage.

    Args:
        test_path (str): Path to specific test file or directory (excluding integration tests)
        with_coverage (bool): Whether to run with coverage
        html_report (bool): Whether to generate HTML coverage report
        min_coverage (int): Minimum required coverage percentage
    """
    # 加载单元测试专用环境变量配置
    env_file = Path(__file__).parent.parent / '.env.unit'
    if env_file.exists():
        load_dotenv(env_file, override=True)
        print(f"已加载单元测试环境变量配置: {env_file}")
    else:
        print(f"警告: 单元测试环境变量文件不存在: {env_file}")

    # 创建环境变量副本用于子进程
    env = os.environ.copy()

    # 验证必需的环境变量是否已设置
    required_env_vars = [
        'WX_APPID',
        'WX_SECRET',
        'TOKEN_SECRET'
    ]

    missing_vars = []
    for var in required_env_vars:
        if var not in env or not env[var]:
            missing_vars.append(var)

    if missing_vars:
        print(f"错误: 缺少必需的环境变量: {', '.join(missing_vars)}")
        print(f"请确保 .env.unit 文件中包含这些环境变量")
        return 1

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