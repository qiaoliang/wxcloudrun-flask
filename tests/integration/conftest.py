"""
pytest配置文件 - integration tests
"""
import sys
import os
import pytest

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture(scope="session")
def test_app():
    """创建测试应用实例"""
    from wxcloudrun import app
    
    # 配置测试环境
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['ENV_TYPE'] = 'test'
    
    return app


@pytest.fixture(scope="session")
def test_db(test_app):
    """创建测试数据库实例"""
    from flask_sqlalchemy import SQLAlchemy
    
    db = SQLAlchemy()
    db.init_app(test_app)
    
    with test_app.app_context():
        yield db


@pytest.fixture(scope="session")
def test_migrate(test_app, test_db):
    """创建Flask-Migrate实例"""
    from flask_migrate import Migrate
    
    migrate = Migrate(test_app, test_db)
    yield migrate


def pytest_configure(config):
    """pytest配置"""
    config.addinivalue_line(
        "markers", "migration: 标记数据库迁移测试"
    )
    config.addinivalue_line(
        "markers", "slow: 标记慢速测试"
    )


def pytest_collection_modifyitems(config, items):
    """修改测试收集"""
    # 为迁移测试添加标记
    for item in items:
        if "migration" in item.nodeid:
            # 使用通用的标记而不是 pytest.markmigration
            item.add_marker(pytest.mark.migration)
        if "performance" in item.nodeid or "large_data" in item.nodeid:
            item.add_marker(pytest.mark.slow)