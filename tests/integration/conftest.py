# 文件: tests/integration/conftest.py

import subprocess
import time
import pytest
import os
from config import DevelopmentConfig # 假设你的 config.py 中有 DevelopmentConfig 包含真实的 DB 配置

def is_docker_available():
    """检查 Docker 是否可用"""
    try:
        result = subprocess.run(["docker", "version"], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE, 
                              check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

# ----------------------------------------------------
# 1. 配置标记
# ----------------------------------------------------

# pytest hook，用于注册自定义标记。
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: mark test as integration test to run against real services."
    )

# ----------------------------------------------------
# 2. 数据库连接夹具
# ----------------------------------------------------

@pytest.fixture(scope='session')
def integration_app():
    """创建一个连接到 Docker 服务的 Flask App 实例"""
    
    # 设置环境为 function 以加载正确的环境变量
    import os
    os.environ['ENV_TYPE'] = 'function'
    
    # Import the app and db after setting environment variables
    from wxcloudrun import app as fresh_flask_app, db as fresh_db
    fresh_flask_app.config['TESTING'] = True
    
    # Store db in app for later use
    fresh_flask_app.db = fresh_db
    
    return fresh_flask_app

@pytest.fixture(scope="session", autouse=True)
def docker_services():
    """
    在整个测试会话开始时启动 Docker 服务，并在会话结束时关闭。
    """
    print("\n--- 启动 Docker Compose 服务... ---")
    # 启动 docker-compose.dev.yml (使用正确的配置文件)
    subprocess.run(["docker-compose", "-f", "docker-compose.dev.yml", "up", "-d"], check=True)

    # 【关键步骤】等待服务启动和健康检查通过
    # 使用 docker-compose ps/log 来检查服务状态
    # 最长等待180秒，每5秒检查一次服务是否启动完成
    max_wait = 180
    check_interval = 5
    waited = 0
    while waited < max_wait:
        # 检查MySQL服务是否已启动
        result = subprocess.run(
            ["docker-compose", "-f", "docker-compose.dev.yml", "ps", "-q", "mysql-db"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.stdout.strip():
            # 容器已启动，再尝试连接数据库确认服务可用
            print("MySQL service container is running, waiting for database to be ready...")
            # 等待数据库完全准备就绪
            time.sleep(10)
            break
        time.sleep(check_interval)
        waited += check_interval
    else:
        subprocess.run(["docker-compose", "-f", "docker-compose.dev.yml", "logs", "mysql-db"], check=True)
        raise RuntimeError("Docker 服务未能在180秒内启动完成")

    yield  # 运行所有测试

    print("\n--- 关闭 Docker Compose 服务... ---")
    # 停止 docker-compose
    subprocess.run(["docker-compose", "-f", "docker-compose.dev.yml", "down"], check=True)

@pytest.fixture(scope='function', autouse=True)
def integration_db_setup(integration_app):
    """
    集成测试的数据库设置：在每次测试前，确保数据库是干净的。
    注意：清理真实数据库比清理内存数据库慢得多。
    """
    with integration_app.app_context():
        # 警告: 在运行集成测试前，确保你的 docker-compose.yml 启动了一个专用的测试数据库！

        # 1. 创建所有表
        integration_app.db.create_all()

        yield # 测试运行

        # 2. 清理数据 (比 drop_all 更快且更安全，但需要模型支持)
        # 如果你的数据库比较大，最好使用事务回滚而不是 drop_all
        # 但对于小项目，drop_all 是最彻底的清理方式
        integration_app.db.session.remove()
        integration_app.db.drop_all()