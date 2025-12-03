#!/usr/bin/env python
"""
功能测试脚本：专门运行 Docker 集成测试，跳过单元测试
基于 run_tests.py 中的集成测试部分提取
"""

import sys
import subprocess
import argparse
import os
import time
import requests
from pathlib import Path

# 添加项目根目录到路径，以便导入config
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置环境类型为功能测试
os.environ['ENV_TYPE'] = 'function'

# 导入配置模块，这将自动加载相应的.env文件
import config


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


def run_functional_tests(with_coverage=False, html_report=False, min_coverage=80, skip_docker=False):
    """
    运行功能测试（Docker集成测试）
    
    Args:
        with_coverage (bool): 是否运行覆盖率测试
        html_report (bool): 是否生成HTML覆盖率报告
        min_coverage (int): 最低覆盖率要求
        skip_docker (bool): 是否跳过Docker启动（假设服务已运行）
    """
    print("🚀 开始功能测试（集成测试）...")
    
    # 通过 config.py 加载环境变量（ENV_TYPE 已设置为 'function'）
    # config.py 会自动加载 .env.function 文件并设置相关环境变量
    
    # 创建环境变量副本
    env = os.environ.copy()
    
    # 设置默认环境变量以跳过微信API测试（自动测试模式）
    # 这些值会被设置为测试值以避免真实微信API调用
    env['WX_APPID'] = 'test_appid'
    env['WX_SECRET'] = 'test_secret'
    env['TOKEN_SECRET'] = 'test_token_secret_for_function_test'
    
    # 使用config.py中的Docker启动超时时间
    docker_startup_timeout = config.DOCKER_STARTUP_TIMEOUT
    print(f"⏰ Docker启动超时时间设置为: {docker_startup_timeout} 秒")
    
    # 启动 docker-compose 服务（除非用户指定跳过）
    if not skip_docker:
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
    else:
        print("\n⏭️ 跳过 Docker 启动（假设服务已运行）...")
        time.sleep(5)  # 给服务一点时间确保稳定
    
    # 运行集成测试
    print("\n🧪 运行 Docker 集成测试...")
    # 设置环境变量以控制是否使用真实微信凭证
    env['USE_REAL_WECHAT_CREDENTIALS'] = 'false'  # 自动测试中默认不使用真实凭证
    print("注意: 微信API测试将被跳过，因为这是自动测试环境。")
    
    integration_test_cmd = [sys.executable, '-m', 'pytest', 'tests/integration_test_counter.py', 'tests/integration_test_supervision_flow.py', '-v']
    
    if with_coverage:
        # For integration tests, run with coverage
        integration_test_cmd = [sys.executable, '-m', 'pytest']
        integration_test_cmd.extend([
            'tests/integration_test_counter.py',
            'tests/integration_test_supervision_flow.py',
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
    
    # 在所有集成测试运行结束后，确保清理docker-compose服务（除非跳过Docker启动）
    if not skip_docker:
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
    else:
        print("\n⏭️ 跳过 Docker 清理（因为跳过了Docker启动）")
    
    if integration_test_result.returncode == 0:
        print("✅ 功能测试通过！")
    else:
        print("❌ Docker 集成测试失败")
    
    return integration_test_result.returncode


def main():
    parser = argparse.ArgumentParser(description='Functional test runner: Docker integration tests only (no unit tests)')
    parser.add_argument('--coverage', action='store_true', help='Run tests with coverage')
    parser.add_argument('--html-report', action='store_true', help='Generate HTML coverage report')
    parser.add_argument('--min-coverage', type=int, default=80, help='Minimum required coverage percentage')
    parser.add_argument('--skip-docker', action='store_true', help='Skip Docker startup/cleanup (assume services are already running)')
    
    args = parser.parse_args()
    
    return run_functional_tests(
        with_coverage=args.coverage,
        html_report=args.html_report,
        min_coverage=args.min_coverage,
        skip_docker=args.skip_docker
    )


if __name__ == '__main__':
    sys.exit(main())