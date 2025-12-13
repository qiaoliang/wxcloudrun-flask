"""
pytest配置文件 - 使用新的数据库架构
完全独立于Flask，支持快速测试
"""
import sys
import os
import pytest
from datetime import datetime

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

# 导入新的数据库模块
from database import initialize_for_test, get_database, reset_all


@pytest.fixture(scope='function')
def test_db():
    """
    为每个测试函数提供干净的数据库
    使用内存数据库，完全独立于Flask
    """
    # 重置数据库确保干净状态
    reset_all()
    
    # 初始化测试数据库
    db = initialize_for_test()
    
    yield db
    
    # 清理（内存数据库会自动清理）


@pytest.fixture(scope='function')
def test_session(test_db):
    """
    提供数据库会话
    自动管理事务和清理
    """
    with test_db.get_session() as session:
        yield session


@pytest.fixture(scope='function')
def test_user(test_session):
    """创建测试用户"""
    from database.models import User
    
    user = User(
        wechat_openid="test_openid_123",
        nickname="测试用户",
        role=1,
        status=1
    )
    test_session.add(user)
    test_session.commit()
    return user


@pytest.fixture(scope='function')
def test_rule(test_session, test_user):
    """创建测试打卡规则"""
    from database.models import CheckinRule
    
    rule = CheckinRule(
        solo_user_id=test_user.user_id,
        rule_name="测试规则",
        status=1
    )
    test_session.add(rule)
    test_session.commit()
    return rule


@pytest.fixture(scope='function')
def test_community(test_session):
    """创建测试社区"""
    from database.models import Community
    
    community = Community(
        name="测试社区",
        location="测试地址",
        status=1
    )
    test_session.add(community)
    test_session.commit()
    return community


@pytest.fixture(scope='function')
def test_superuser(test_session):
    """创建超级管理员用户"""
    from database.models import User
    
    user = User(
        wechat_openid="super_admin_test",
        nickname="超级管理员",
        role=4,
        status=1
    )
    test_session.add(user)
    test_session.commit()
    return user


# 为了向后兼容，保留原有的test_app fixture
# 但它现在只提供最小的Flask应用，不包含数据库
@pytest.fixture(scope='session')
def test_app():
    """
    兼容性fixture：最小化的Flask应用
    注意：不包含数据库功能，使用test_db或test_session进行数据库测试
    """
    from flask import Flask
    
    app = Flask(__name__)
    app.config['TESTING'] = True
    
    class MinimalFlaskApp:
        def __init__(self, app):
            self.app = app
            self.app_context = self.AppContext(app)
        
        class AppContext:
            def __init__(self, app):
                self.app = app
            def __enter__(self):
                return self.app.app_context().__enter__()
            def __exit__(self, *args):
                return self.app.app_context().__exit__(*args)
        
        def test_client(self):
            raise NotImplementedError(
                "完整Flask功能不可用。请使用test_db或test_session进行数据库测试。"
            )
    
    return MinimalFlaskApp(app)


@pytest.fixture(scope='function')
def test_db_legacy(test_db):
    """
    兼容性fixture：提供与原有接口相同的数据库对象
    内部使用新的数据库架构
    """
    class DatabaseWrapper:
        def __init__(self, db_core):
            self._db = db_core
        
        @property
        def session(self):
            # 返回一个会话上下文管理器
            return self._db.get_session().__enter__()
        
        def create_all(self):
            self._db.create_tables()
        
        def drop_all(self):
            self._db.drop_tables()
    
    return DatabaseWrapper(test_db)