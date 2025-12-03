import pytest
import os
import subprocess
import time
from wxcloudrun import app as flask_app
from wxcloudrun import db
from config import DevelopmentConfig # 假设真实配置在这里

# ----------------------------------------------------------------------
# 1. Pytest 标记注册 (必须)
# ----------------------------------------------------------------------

def pytest_configure(config):
    """注册 integration 标记"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test to run against real services."
    )

# ----------------------------------------------------------------------
# 2. Docker 环境管理 (可选，用于自动化)
# ----------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def docker_services_setup():
    """
    【Session 级别】自动启动和关闭 docker-compose 服务。
    注意：这需要你的 pytest 运行在项目根目录。
    """
    print("\n--- [集成测试] 启动 Docker Compose 服务... ---")
    try:
        # 启动 docker-compose (假设你在根目录运行)
        subprocess.run(["docker-compose", "up", "-d"], check=True)
        # 等待服务启动 (MySQL/Redis 启动需要时间)
        time.sleep(8)
        print("--- Docker 服务已就绪。---")
        yield # 运行测试
    finally:
        print("\n--- [集成测试] 关闭 Docker Compose 服务... ---")
        subprocess.run(["docker-compose", "down"], check=True)

# ----------------------------------------------------------------------
# 3. 覆盖核心 Fixture (连接真实 DB)
# ----------------------------------------------------------------------

# 覆盖顶层 conftest.py 中的 app Fixture
@pytest.fixture(scope='session')
def app():
    """
    【覆盖】创建连接到 Docker MySQL/Redis 的 Flask 应用实例。
    """
    # 1. 继承真实配置
    # 注意：确保你的 docker-compose.yml 服务名称（如 'mysql'）与配置匹配
    flask_app.config.from_object(DevelopmentConfig)

    # 2. 如果你的 DB URI 在 config.py 中依赖环境变量，这里确保设置
    # flask_app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_TEST_URI', 'mysql+pymysql://user:pass@mysql:3306/test_db')

    flask_app.config['TESTING'] = True

    yield flask_app

# 注意：
# 1. integration/ 的测试会使用这个 app Fixture，它连接的是 Docker DB。
# 2. 它仍然会使用顶层 conftest.py 的 db_session_setup Fixture 进行建表和清表，但操作的是 Docker DB。