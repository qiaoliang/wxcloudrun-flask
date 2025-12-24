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

# 导入测试数据生成器
from wxcloudrun.test_data_generator import (
    generate_unique_phone_number,
    generate_unique_openid,
    generate_unique_nickname,
    generate_unique_username
)
from hashlib import sha256


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
        wechat_openid=generate_unique_openid("13900008000", "test_user"),
        phone_number=generate_unique_phone_number("test_user"),
        phone_hash=sha256(f"default_secret:{generate_unique_phone_number('test_user')}".encode('utf-8')).hexdigest(),
        nickname=generate_unique_nickname("test_user"),
        name=generate_unique_username("test_user"),
        role=1,
        status=1
    )
    test_session.add(user)
    test_session.commit()
    return user


@pytest.fixture(scope='function')
def test_rule(test_session, test_user):
    """创建测试打卡规则"""
    # 先创建一个默认社区
    community = Community(
        name="默认测试社区",
        status=1
    )
    test_session.add(community)
    test_session.flush()
    
    rule = CheckinRule(
        user_id=test_user.user_id,
        community_id=community.community_id,
        rule_type="personal",
        rule_name="测试规则",
        status=1
    )
    test_session.add(rule)
    test_session.commit()
    return rule


@pytest.fixture(scope='function')
def test_community(test_session):
    """创建测试社区"""
    community = Community(
        name=f"community_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        description="单元测试社区",
        status=1
    )
    test_session.add(community)
    test_session.commit()
    return community


@pytest.fixture(scope='function')
def test_superuser(test_session):
    """创建超级管理员用户"""
    user = User(
        wechat_openid=generate_unique_openid("13900008001", "test_superuser"),
        phone_number=generate_unique_phone_number("test_superuser"),
        phone_hash=sha256(f"default_secret:{generate_unique_phone_number('test_superuser')}".encode('utf-8')).hexdigest(),
        nickname=generate_unique_nickname("test_superuser"),
        name=generate_unique_username("test_superuser"),
        role=4,
        status=1
    )
    test_session.add(user)
    test_session.commit()
    return user


def create_test_user(test_session, role=1, test_context="test_user"):
    """
    创建测试用户的通用函数
    
    Args:
        test_session: 数据库会话
        role: 用户角色，默认为1（普通用户）
        test_context: 测试上下文，用于生成唯一数据
        
    Returns:
        创建的用户对象
    """
    phone = generate_unique_phone_number(test_context)
    user = User(
        wechat_openid=generate_unique_openid(phone, test_context),
        phone_number=phone,
        phone_hash=sha256(f"default_secret:{phone}".encode('utf-8')).hexdigest(),
        nickname=generate_unique_nickname(test_context),
        name=generate_unique_username(test_context),
        role=role,
        status=1
    )
    test_session.add(user)
    test_session.commit()
    return user


def create_test_community(test_session, name_suffix=None):
    """
    创建测试社区的通用函数
    
    Args:
        test_session: 数据库会话
        name_suffix: 名称后缀，如果为None则使用时间戳
        
    Returns:
        创建的社区对象
    """
    if name_suffix is None:
        name_suffix = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    community = Community(
        name=f"community_{name_suffix}",
        description=f"单元测试社区_{name_suffix}",
        status=1
    )
    test_session.add(community)
    test_session.commit()
    return community


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

