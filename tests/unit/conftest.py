"""
pytest配置文件 - 支持Flask-SQLAlchemy架构
提供Flask应用上下文和数据库支持
"""
import sys
import os
import pytest
from datetime import datetime

# 设置测试环境变量
os.environ['ENV_TYPE'] = 'unit'

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

# 导入Flask-SQLAlchemy相关模块
from flask import Flask
from database.flask_models import db, User, Community, CheckinRule, CheckinRecord, UserAuditLog


@pytest.fixture(scope='function')
def test_session(test_app):
    """
    提供Flask-SQLAlchemy数据库会话
    在Flask应用上下文中工作
    """
    with test_app.app_context():
        yield db.session


@pytest.fixture(scope='function')
def test_user(test_session):
    """创建测试用户"""
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
    rule = CheckinRule(
        user_id=test_user.user_id,
        rule_type="测试规则",
        is_active=True
    )
    test_session.add(rule)
    test_session.commit()
    return rule


@pytest.fixture(scope='function')
def test_community(test_session):
    """创建测试社区"""
    community = Community(
        name="测试社区",
        status=1
    )
    test_session.add(community)
    test_session.commit()
    return community


@pytest.fixture(scope='function')
def test_superuser(test_session):
    """创建超级管理员用户"""
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
@pytest.fixture(scope='function')
def test_app():
    """
    提供Flask应用上下文和数据库
    支持Flask-SQLAlchemy架构
    """
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化Flask-SQLAlchemy
    db.init_app(app)
    
    with app.app_context():
        # 创建所有表
        db.create_all()
        yield app
        # 清理
        db.drop_all()

