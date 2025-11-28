# tests/conftest.py
import os
import time
import requests
import subprocess
import pytest
from typing import Generator

# 在导入应用前设置测试环境变量
os.environ['USE_SQLITE_FOR_TESTING'] = 'true'
os.environ['PYTEST_CURRENT_TEST'] = '1'

from wxcloudrun import app as original_app, db
from wxcloudrun.model import Counters


@pytest.fixture(scope="session")
def docker_compose_env() -> Generator[str, None, None]:
    """
    启动 docker-compose 开发环境的 session 级 fixture
    这个 fixture 会在所有测试开始前启动一次，在所有测试结束后停止
    """
    # 检查是否需要运行 Docker 集成测试
    run_docker_integration_tests = os.environ.get("RUN_DOCKER_INTEGRATION_TESTS", "false").lower() == "true"
    
    if not run_docker_integration_tests:
        # 如果不需要运行 Docker 集成测试，跳过 Docker 启动
        yield "http://localhost:8080"
        return
    
    # 检查 docker-compose 文件是否存在
    if not os.path.exists("docker-compose.dev.yml"):
        pytest.skip("docker-compose.dev.yml 文件不存在，跳过集成测试")
    
    # 设置环境变量
    env_vars = {
        "MYSQL_PASSWORD": os.environ.get("MYSQL_PASSWORD", "rootpassword"),
        "WX_APPID": os.environ.get("WX_APPID", "test_appid"),
        "WX_SECRET": os.environ.get("WX_SECRET", "test_secret"),
        "TOKEN_SECRET": "42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f",
        "DOCKER_STARTUP_TIMEOUT": os.environ.get("DOCKER_STARTUP_TIMEOUT", "180")
    }
    
    # 创建临时的 .env 文件
    env_content = "\n".join([f"{k}={v}" for k, v in env_vars.items()])
    with open(".env.test", "w") as f:
        f.write(env_content)
    
    try:
        # 停止可能存在的服务
        subprocess.run([
            "docker-compose", "-f", "docker-compose.dev.yml", "down", "--remove-orphans"
        ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 启动开发环境
        compose_process = subprocess.Popen([
            "docker-compose", "-f", "docker-compose.dev.yml", "up", "--build", "-d"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 获取Docker启动超时时间
        timeout = int(os.environ.get("DOCKER_STARTUP_TIMEOUT", "180"))
        
        # 等待服务启动
        base_url = "http://localhost:8080"
        if not wait_for_service(f"{base_url}/", timeout=timeout):
            raise RuntimeError("服务启动超时")
        
        # 等待 MySQL 服务完全准备就绪
        time.sleep(15)
        
        yield base_url  # 提供服务 URL 给测试用例
        
    finally:
        # 清理：停止 docker-compose 服务
        subprocess.run([
            "docker-compose", "-f", "docker-compose.dev.yml", "down", "--remove-orphans"
        ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 删除临时 .env 文件
        if os.path.exists(".env.test"):
            os.remove(".env.test")


def wait_for_service(url: str, timeout: int = 60) -> bool:
    """
    等待服务启动
    :param url: 服务 URL
    :param timeout: 超时时间（秒）
    :return: 是否成功连接
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(2)
    return False


@pytest.fixture
def client():
    """Create a test client for the app."""
    app = original_app
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # 初始化一个计数器，确保初始值为0
            initial_counter = Counters(count=0)
            db.session.add(initial_counter)
            db.session.commit()
            yield client