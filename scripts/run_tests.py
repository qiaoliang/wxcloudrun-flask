#!/usr/bin/env python
"""
完整测试流程脚本：先运行单元测试，成功后再运行 Docker 集成测试
"""

import sys
import subprocess
import argparse
import os
import time
import requests
from pathlib import Path

# 添加脚本目录到路径，以便导入load_env
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from load_env import load_env_file, get_env_with_defaults


def wait_for_service(base_url: str, timeout: int = 180) -> bool:
    """
    等待服务启动
    :param base_url: 服务基本URL
    :param timeout: 超时时间（秒）
    :return: 是否成功连接
    """
    print(f"⏳ 等待服务启动... 最大等待时间: {timeout} 秒")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{base_url}/", timeout=5)
            if response.status_code == 200:
                print("✅ 服务启动成功")
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(2)
        print(f"⏳ 继续等待... 已等待 {int(time.time() - start_time)} 秒")
    
    print(f"❌ 服务启动超时，等待了 {timeout} 秒")
    return False


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
    
    # 加载集成测试环境变量配置
    load_env_file(".env.integration")  # 集成测试专用环境变量文件
    load_env_file(".env")  # 加载主环境变量文件
    
    # 设置默认环境变量以跳过微信API测试（自动测试模式）
    default_env = {
        'WX_APPID': 'test_appid',  # 默认值，会导致跳过微信API测试
        'WX_SECRET': 'test_secret',  # 默认值，会导致跳过微信API测试
        'TOKEN_SECRET': '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f',
        'DOCKER_STARTUP_TIMEOUT': '180'  # 默认启动超时时间为180秒
    }
    
    # 获取环境变量，未设置的使用默认值
    env_vars = get_env_with_defaults(default_env)
    
    # 创建环境变量副本并更新
    env = os.environ.copy()
    env.update(env_vars)
    
    # 获取Docker启动超时时间
    docker_startup_timeout = int(env.get('DOCKER_STARTUP_TIMEOUT', '180'))
    print(f"⏰ Docker启动超时时间设置为: {docker_startup_timeout} 秒")
    
    # 启动 docker-compose 服务
    print("\n🐳 启动 Docker 服务...")
    print("注意: 这将启动 docker-compose 服务，请确保 Docker 正在运行。")
    
    try:
        # 停止可能存在的服务
        subprocess.run([
            "docker-compose", "-f", "docker-compose.dev.yml", "down", "--remove-orphans"
        ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 启动开发环境
        compose_process = subprocess.Popen([
            "docker-compose", "-f", "docker-compose.dev.yml", "up", "--build", "-d"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 等待服务启动
        base_url = "http://localhost:8080"
        if not wait_for_service(base_url, timeout=docker_startup_timeout):
            print("❌ Docker服务启动失败，跳过集成测试")
            return 1
        
        # 等待 MySQL 服务完全准备就绪
        print("⏳ 等待数据库服务完全准备就绪...")
        time.sleep(15)
        
    except Exception as e:
        print(f"❌ 启动 Docker 服务时出错: {e}")
        return 1
    
    # 第二步：运行集成测试（仅当单元测试通过时）
    print("\n🧪 运行 Docker 集成测试...")
    # 设置环境变量以控制是否使用真实微信凭证
    env['USE_REAL_WECHAT_CREDENTIALS'] = 'false'  # 自动测试中默认不使用真实凭证
    print("注意: 微信API测试将被跳过，因为这是自动测试环境。")
    
    integration_test_cmd = [sys.executable, '-m', 'pytest', 'tests/integration_test_counter.py', 'tests/integration_test_login.py', '-v']
    
    if with_coverage:
        # For integration tests, run with coverage
        integration_test_cmd = [sys.executable, '-m', 'pytest']
        integration_test_cmd.extend([
            'tests/integration_test_counter.py',
            'tests/integration_test_login.py',
            '--cov=wxcloudrun',
            f'--cov-fail-under={min_coverage}'
        ])
        if html_report:
            integration_test_cmd.extend(['--cov-report=html', '--cov-report=term-missing'])
        else:
            integration_test_cmd.extend(['--cov-report=term-missing'])
        integration_test_cmd.append('-v')
    
    print(f"运行 Docker 集成测试命令: {' '.join(integration_test_cmd)}")
    integration_test_result = subprocess.run(integration_test_cmd, env=env)
    
    # 在所有集成测试运行结束后，确保清理docker-compose服务
    print("\n🧹 清理 Docker 服务...")
    try:
        # 尝试停止可能仍在运行的开发环境服务
        # 使用绝对路径确保能够正确执行
        subprocess.run([
            "docker-compose", "-f", "docker-compose.dev.yml", "down", "--remove-orphans"
        ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 同时也尝试停止主 docker-compose.yml 中定义的服务
        # (如果存在的话，以防某些测试使用了主配置)
        subprocess.run([
            "docker-compose", "-f", "docker-compose.yml", "down", "--remove-orphans"
        ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print("✅ Docker 服务已清理")
    except Exception as e:
        print(f"⚠️ 清理 Docker 服务时出错: {e}")
    
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