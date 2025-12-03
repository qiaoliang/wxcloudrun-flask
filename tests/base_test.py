# tests/base_test.py
"""
Base test class for API tests
"""
import pytest
import json
import jwt
import datetime
from wxcloudrun import db
from wxcloudrun.model import User, CheckinRule, RuleSupervision


class BaseTest:
    """Base test class with common utilities"""
    
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