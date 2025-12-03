import pytest
import os
from wxcloudrun import app as flask_app  # 假设你的应用实例在这里
from wxcloudrun import db  # 假设你的 SQLAlchemy 实例在这里

# ----------------------------------------------------------------------
# 核心 Fixture (默认用于单元测试：内存数据库)
# ----------------------------------------------------------------------

@pytest.fixture(scope='session')
def app():
    """
    【Session 级别】创建 Flask 应用实例。
    默认配置为 SQLite 内存数据库，适用于所有单元测试。
    """

    # 强制开启测试模式
    flask_app.config['TESTING'] = True

    # 关键：将数据库 URI 指向内存中的 SQLite (用于单元测试隔离)
    # 这将在 integration/conftest.py 中被覆盖
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    # 启用日志静默等测试相关配置
    flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 如果有其他配置，例如 SECRET_KEY 等，在这里设置测试值

    # 返回配置好的应用实例
    yield flask_app

@pytest.fixture
def client(app):
    """
    【函数 级别】创建测试客户端。
    用于模拟 HTTP 请求。
    """
    # 使用 app.test_client() 创建客户端
    return app.test_client()


# ----------------------------------------------------------------------
# 数据库生命周期 Fixture (所有测试都会自动使用它来设置数据库)
# ----------------------------------------------------------------------

# 注意：autouse=True 会自动应用于所有测试，除非被子目录的 conftest 覆盖或禁用。
@pytest.fixture(autouse=True)
def db_session_setup(app):
    """
    【函数 级别】数据库会话清理和表结构设置。
    """
    with app.app_context():
        # 1. 启动事务并建表
        db.create_all()

        # 2. 如果你的测试使用了事务回滚，可以在这里开始事务
        # db.session.begin_nested()

        yield  # 测试函数在这里运行

        # 3. 清理：移除会话并销毁表
        db.session.remove()
        db.drop_all()