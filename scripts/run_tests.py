#!/usr/bin/env python
"""
完整测试流程脚本：先运行单元测试，成功后再运行 Docker 集成测试
"""

import sys
import subprocess
import argparse


def run_complete_test_suite(with_coverage=False, html_report=False, min_coverage=80):
    """
    Run complete test suite: unit tests first, then integration tests if unit tests pass.
    
    Args:
        with_coverage (bool): Whether to run with coverage
        html_report (bool): Whether to generate HTML coverage report
        min_coverage (int): Minimum required coverage percentage
    """
    print("🚀 开始完整测试流程...")
    
    # 第一步：运行单元测试
    print("\n🔍 运行单元测试...")
    
    unit_test_cmd = [sys.executable, 'scripts/unit_tests.py']
    if with_coverage:
        unit_test_cmd.append('--coverage')
        unit_test_cmd.append(f'--min-coverage={min_coverage}')
        if html_report:
            # For unit tests with coverage, we need to handle the html report differently
            unit_test_cmd.append('--html-report')
    
    print(f"运行单元测试命令: {' '.join(unit_test_cmd)}")
    unit_test_result = subprocess.run(unit_test_cmd)
    
    if unit_test_result.returncode != 0:
        print("❌ 单元测试失败，跳过集成测试")
        return unit_test_result.returncode
    else:
        print("✅ 单元测试通过，开始运行 Docker 集成测试...")
    
    # 第二步：运行集成测试（仅当单元测试通过时）
    print("\n🐳 运行 Docker 集成测试...")
    
    integration_test_cmd = [sys.executable, '-m', 'pytest', 'tests/integration_test_docker.py', '-v']
    
    if with_coverage:
        # For integration tests, run with coverage
        integration_test_cmd = [sys.executable, '-m', 'pytest']
        integration_test_cmd.extend([
            'tests/integration_test_docker.py',
            '--cov=wxcloudrun',
            f'--cov-fail-under={min_coverage}'
        ])
        if html_report:
            integration_test_cmd.extend(['--cov-report=html', '--cov-report=term-missing'])
        else:
            integration_test_cmd.extend(['--cov-report=term-missing'])
        integration_test_cmd.append('-v')
    
    print(f"运行 Docker 集成测试命令: {' '.join(integration_test_cmd)}")
    print("注意: 这将启动 docker-compose 服务，请确保 Docker 正在运行。")
    integration_test_result = subprocess.run(integration_test_cmd)
    
    if integration_test_result.returncode == 0:
        print("✅ 所有测试通过！")
    else:
        print("❌ Docker 集成测试失败")
    
    return integration_test_result.returncode


def main():
    parser = argparse.ArgumentParser(description='Complete test suite runner: unit tests first, then Docker integration tests if unit tests pass')
    parser.add_argument('--coverage', action='store_true', help='Run tests with coverage')
    parser.add_argument('--html-report', action='store_true', help='Generate HTML coverage report')
    parser.add_argument('--min-coverage', type=int, default=80, help='Minimum required coverage percentage')
    
    args = parser.parse_args()
    
    return run_complete_test_suite(
        with_coverage=args.coverage,
        html_report=args.html_report,
        min_coverage=args.min_coverage
    )


if __name__ == '__main__':
    sys.exit(main())