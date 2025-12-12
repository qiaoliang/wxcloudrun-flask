"""
pytest配置文件 - unit tests
"""
import sys
import os
import pytest
from datetime import datetime

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from wxcloudrun import app, db
from wxcloudrun.model import User, CheckinRule, CheckinRecord, SupervisionRuleRelation


@pytest.fixture(scope='session')
def test_app():
    """创建测试应用"""
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'WTF_CSRF_ENABLED': False
    })
    
    with app.app_context():
        # 创建所有数据库表
        db.create_all()
        yield app
        # 清理
        db.drop_all()


@pytest.fixture(scope='function')
def test_db(test_app):
    """为每个测试函数提供干净的数据库"""
    with test_app.app_context():
        yield db
        # 清理所有表
        SupervisionRuleRelation.query.delete()
        CheckinRecord.query.delete()
        CheckinRule.query.delete()
        User.query.delete()
        db.session.commit()


@pytest.fixture(scope='function')
def test_user(test_db):
    """创建测试用户"""
    user = User(
        wechat_openid="test_openid_123",
        nickname="测试用户",
        role=1  # 独居者
    )
    test_db.session.add(user)
    test_db.session.commit()
    return user


@pytest.fixture(scope='function')
def test_rule(test_db, test_user):
    """创建测试打卡规则"""
    rule = CheckinRule(
        solo_user_id=test_user.user_id,
        rule_name="测试规则",
        status=1
    )
    test_db.session.add(rule)
    test_db.session.commit()
    return rule


@pytest.fixture(scope='function')
def test_client(test_app):
    """创建测试客户端"""
    return test_app.test_client()