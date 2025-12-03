# tests/base_test.py
"""
Base test class for API tests
"""
import pytest
import json
import jwt
import datetime
from wxcloudrun import db
from wxcloudrun.model import User, CheckinRule, RuleSupervision, Counters


class BaseTest:
    """测试基类，提供数据库隔离"""
    
    @classmethod
    def setup_class(cls):
        """类级别的设置"""
        pass
    
    def ensure_clean_database(self):
        """确保数据库是空的"""
        # 删除所有可能残留的数据
        RuleSupervision.query.delete()
        CheckinRule.query.delete()
        User.query.delete()
        Counters.query.delete()
        db.session.commit()
    
    @staticmethod
    def create_auth_token(user_id, secret_key='42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f'):
        """Create JWT auth token for testing"""
        token_payload = {
            'user_id': user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        return jwt.encode(token_payload, secret_key, algorithm='HS256')
    
    def create_user(self, **kwargs):
        """创建测试用户"""
        defaults = {
            'phone_number': '13800000001',
            'nickname': '测试用户',
            'is_solo_user': True,
            'is_supervisor': False,
            'status': 1,
            'auth_type': 'phone'
        }
        defaults.update(kwargs)
        user = User(**defaults)
        db.session.add(user)
        db.session.commit()
        return user
    
    def create_checkin_rule(self, solo_user_id, **kwargs):
        """创建打卡规则"""
        from datetime import time
        defaults = {
            'solo_user_id': solo_user_id,
            'rule_name': '测试打卡',
            'icon_url': '🌅',
            'frequency_type': 0,
            'time_slot_type': 4,
            'custom_time': time(8, 0, 0),
            'week_days': 127,
            'status': 1
        }
        defaults.update(kwargs)
        rule = CheckinRule(**defaults)
        db.session.add(rule)
        db.session.commit()
        return rule
    
    def create_supervision(self, rule_id, solo_user_id, supervisor_user_id, **kwargs):
        """创建监护关系"""
        defaults = {
            'rule_id': rule_id,
            'solo_user_id': solo_user_id,
            'supervisor_user_id': supervisor_user_id,
            'status': 0,
            'invitation_message': '请监督我',
            'invited_by_user_id': solo_user_id
        }
        defaults.update(kwargs)
        supervision = RuleSupervision(**defaults)
        db.session.add(supervision)
        db.session.commit()
        return supervision
    
    @staticmethod
    def cleanup_test_data():
        """Clean up test data (deprecated, use ensure_clean_database instead)"""
        RuleSupervision.query.delete()
        CheckinRule.query.delete()
        User.query.delete()
        db.session.commit()


# 保持向后兼容的旧基类
class LegacyBaseTest:
    """Legacy base test class with common utilities (not isolated)"""
    
    @staticmethod
    def create_auth_token(user_id, secret_key='42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f'):
        """Create JWT auth token for testing"""
        token_payload = {
            'user_id': user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        return jwt.encode(token_payload, secret_key, algorithm='HS256')
    
    @staticmethod
    def create_test_user(phone_number, nickname, is_solo_user=True, is_supervisor=False, status=1):
        """Create a test user"""
        user = User(
            phone_number=phone_number,
            nickname=nickname,
            is_solo_user=is_solo_user,
            is_supervisor=is_supervisor,
            status=status,
            auth_type='phone'
        )
        db.session.add(user)
        db.session.commit()
        return user
    
    @staticmethod
    def create_test_rule(solo_user_id, rule_name, icon_url='🌅', custom_time='08:00:00'):
        """Create a test check-in rule"""
        from datetime import time
        rule = CheckinRule(
            solo_user_id=solo_user_id,
            rule_name=rule_name,
            icon_url=icon_url,
            frequency_type=0,
            time_slot_type=4,
            custom_time=time(8, 0, 0),
            week_days=127,
            status=1
        )
        db.session.add(rule)
        db.session.commit()
        return rule
    
    @staticmethod
    def create_test_supervision(rule_id, solo_user_id, supervisor_user_id, status=0, message='请监督我'):
        """Create a test supervision relationship"""
        supervision = RuleSupervision(
            rule_id=rule_id,
            solo_user_id=solo_user_id,
            supervisor_user_id=supervisor_user_id,
            status=status,
            invitation_message=message,
            invited_by_user_id=solo_user_id
        )
        db.session.add(supervision)
        db.session.commit()
        return supervision
    
    @staticmethod
    def cleanup_test_data():
        """Clean up test data"""
        RuleSupervision.query.delete()
        CheckinRule.query.delete()
        User.query.delete()
        db.session.commit()