"""
测试账号合并功能 (pytest版本)
"""
import sys
import os
from datetime import datetime, timedelta

import pytest

# 添加src路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from wxcloudrun import db, app
from wxcloudrun.model import User, CheckinRule, CheckinRecord, SupervisionRuleRelation
from wxcloudrun.views import _merge_accounts_by_time


@pytest.fixture
def setup_db():
    """设置测试数据库"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()


class TestAccountMerging:
    """账号合并功能测试"""
    
    def test_merge_accounts_by_time_earlier_wins(self, setup_db):
        """测试按注册时间合并，较早的账号获胜"""
        # 创建两个用户，第一个更早，只有微信
        earlier_user = User(
            wechat_openid="early_wx",
            phone_hash=None,
            nickname="Early User",
            role=1,
            status=1,
            created_at=datetime.now() - timedelta(days=2)
        )
        # 第二个较晚，只有手机号
        later_user = User(
            wechat_openid="later_wx_temp",
            phone_hash="late_phone",
            phone_number="138****0001",
            nickname="Later User",
            role=1,
            status=1,
            created_at=datetime.now() - timedelta(days=1)
        )
        
        db.session.add(earlier_user)
        db.session.add(later_user)
        db.session.commit()
        
        # 为较早用户添加一些数据
        rule1 = CheckinRule(
            solo_user_id=earlier_user.user_id,
            rule_name="Morning Check",
            status=1
        )
        db.session.add(rule1)
        
        # 为较晚用户添加一些数据
        rule2 = CheckinRule(
            solo_user_id=later_user.user_id,
            rule_name="Evening Check",
            status=1
        )
        db.session.add(rule2)
        db.session.commit()
        
        # 合并账号
        primary = _merge_accounts_by_time(earlier_user, later_user)
        
        # 验证结果
        assert primary.user_id == earlier_user.user_id
        assert primary.wechat_openid == "early_wx"
        assert primary.phone_hash == "late_phone"  # 应该从较晚用户继承
        assert primary.phone_number == "138****0001"
        
        # 验证数据迁移
        rules = CheckinRule.query.filter_by(solo_user_id=primary.user_id).all()
        assert len(rules) == 2
        
        # 验证较晚用户被禁用
        disabled_user = User.query.filter_by(user_id=later_user.user_id).first()
        assert disabled_user.status == 2
        assert disabled_user.phone_hash != "late_phone"  # phone_hash应该被清空
    
    def test_merge_accounts_by_time_later_wins(self, setup_db):
        """测试按注册时间合并，较早的账号获胜"""
        # 创建两个用户，第二个更早
        later_user = User(
            wechat_openid="later_wx2",
            phone_hash=None,
            nickname="Later User",
            role=1,
            status=1,
            created_at=datetime.now() - timedelta(days=1)
        )
        earlier_user = User(
            wechat_openid="early_wx2",
            phone_hash="early_phone2",
            phone_number="138****0002",
            nickname="Earlier User",
            role=1,
            status=1,
            created_at=datetime.now() - timedelta(days=2)
        )
        
        db.session.add(later_user)
        db.session.add(earlier_user)
        db.session.commit()
        
        # 合并账号
        primary = _merge_accounts_by_time(later_user, earlier_user)
        
        # 验证结果 - 较早的用户应该获胜
        assert primary.user_id == earlier_user.user_id
        assert primary.wechat_openid == "early_wx2"  # 较早用户的wechat_openid保留
        assert primary.phone_hash == "early_phone2"
        assert primary.phone_number == "138****0002"