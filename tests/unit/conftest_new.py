"""
pytest配置文件 - unit tests
使用最小化Flask依赖的数据库初始化
"""
import sys
import os
import pytest

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

# 使用最小化数据库初始化器
from minimal_db_initializer import get_test_db_initializer, reset_test_db


@pytest.fixture(scope='session')
def db_engine():
    """创建数据库引擎（session级别，所有测试共享）"""
    initializer = get_test_db_initializer()
    engine, session_factory = initializer.initialize()
    yield engine
    # 清理
    engine.dispose()


@pytest.fixture(scope='function')
def db_session(db_engine):
    """
    为每个测试函数提供干净的数据库会话
    使用与生产相同的模型结构，但最小化Flask依赖
    """
    initializer = get_test_db_initializer()
    
    with initializer.get_session() as session:
        # 创建基础测试数据（模拟生产环境）
        initializer.create_test_data(session)
        
        yield session
        
        # 清理：删除所有测试数据
        try:
            # 按依赖关系顺序删除数据
            from wxcloudrun.model import (
                SupervisionRuleRelation, CheckinRecord, CheckinRule,
                CommunityStaff, CommunityMember, Community, User
            )
            
            # 删除关系数据
            session.query(SupervisionRuleRelation).delete()
            session.query(CheckinRecord).delete()
            session.query(CommunityStaff).delete()
            session.query(CommunityMember).delete()
            
            # 删除实体数据
            session.query(CheckinRule).delete()
            session.query(Community).delete()
            session.query(User).delete()
            
            session.commit()
        except Exception:
            session.rollback()
            # 如果清理失败，重新初始化
            reset_test_db()
            initializer.initialize()


@pytest.fixture(scope='function')
def test_user(db_session):
    """创建测试用户"""
    from wxcloudrun.model import User
    
    user = User(
        wechat_openid="test_openid_123",
        nickname="测试用户",
        role=1  # 独居者
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture(scope='function')
def test_rule(db_session, test_user):
    """创建测试打卡规则"""
    from wxcloudrun.model import CheckinRule
    
    rule = CheckinRule(
        solo_user_id=test_user.user_id,
        rule_name="测试规则",
        status=1
    )
    db_session.add(rule)
    db_session.commit()
    return rule


@pytest.fixture(scope='function')
def test_community(db_session):
    """创建测试社区"""
    from wxcloudrun.model import Community
    
    community = Community(
        name="测试社区",
        location="测试地址",
        status=1
    )
    db_session.add(community)
    db_session.commit()
    return community


# 为了向后兼容，保留原有的test_app和test_db fixture
# 但它们现在使用最小化的初始化方式
@pytest.fixture(scope='session')
def test_app():
    """
    兼容性fixture：最小化的Flask应用
    注意：这个fixture只提供数据库功能，不提供完整的Flask功能
    """
    # 返回一个模拟的Flask应用对象
    class MinimalFlaskApp:
        def __init__(self):
            self.app_context = self.AppContext()
        
        class AppContext:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        
        def test_client(self):
            raise NotImplementedError(
                "完整Flask功能不可用。请使用db_session fixture进行数据库测试。"
            )
    
    return MinimalFlaskApp()


@pytest.fixture(scope='function')
def test_db(db_session):
    """
    兼容性fixture：提供与原有接口相同的数据库对象
    内部使用db_session实现
    """
    class DatabaseWrapper:
        def __init__(self, session):
            self.session = session
        
        @property
        def session(self):
            return self._session
    
    return DatabaseWrapper(db_session)