# tests/conftest_isolated.py
"""
支持数据库隔离的测试配置
每个测试类使用独立的数据库实例
"""

import os
import uuid
import pytest
from typing import Generator

# 设置测试环境
os.environ['PYTEST_CURRENT_TEST'] = '1'
os.environ['ENV_TYPE'] = 'unit'

from wxcloudrun import app as original_app, db
from wxcloudrun.model import Counters, User, CheckinRule, RuleSupervision


@pytest.fixture(scope="class")
def isolated_database():
    """
    为每个测试类提供完全隔离的数据库实例
    
    这个 fixture 会：
    1. 创建新的内存数据库
    2. 只创建表结构（schema），不插入任何数据
    3. 在测试类结束后清理数据库
    """
    # 生成唯一的数据库标识，用于调试
    db_id = f"isolated_db_{uuid.uuid4().hex[:8]}"
    
    # 保存原始配置
    original_uri = original_app.config.get('SQLALCHEMY_DATABASE_URI')
    
    try:
        # 配置使用内存数据库
        original_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        original_app.config['TESTING'] = True
        
        with original_app.app_context():
            # 只创建表结构，不插入任何数据
            db.create_all()
            
            # 验证数据库是空的
            assert Counters.query.count() == 0
            assert User.query.count() == 0
            assert CheckinRule.query.count() == 0
            assert RuleSupervision.query.count() == 0
            
            yield original_app
            
            # 清理：删除所有表
            db.drop_all()
            
    finally:
        # 恢复原始配置
        original_app.config['SQLALCHEMY_DATABASE_URI'] = original_uri


@pytest.fixture(scope="class")
def isolated_client(isolated_database):
    """
    为每个测试类提供使用隔离数据库的测试客户端
    """
    app = isolated_database
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            yield client


# 保持原有的 session 级 fixture，用于集成测试
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

    import time
    import requests
    import subprocess

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
    import time
    import requests
    
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


# 保留原有的 client fixture，用于非隔离测试
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