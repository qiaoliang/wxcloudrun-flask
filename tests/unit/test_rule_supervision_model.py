"""
Test cases for SupervisionRuleRelation model and related functionality
"""
import pytest
from datetime import datetime
from wxcloudrun.model import User, CheckinRule, SupervisionRuleRelation
from wxcloudrun import db


class TestSupervisionRuleRelationModel:
    """Test cases for SupervisionRuleRelation model"""

    def test_supervision_rule_relation_creation(self, test_db):
        """Test creating a supervision rule relation"""
        # Create test users
        user1 = User(
            wechat_openid='test_openid_1',
            nickname='Test User 1',
            role=1,  # solo user
            status=1
        )
        user2 = User(
            wechat_openid='test_openid_2',
            nickname='Test User 2',
            role=2,  # supervisor
            status=1
        )
        
        test_db.session.add(user1)
        test_db.session.add(user2)
        test_db.session.flush()  # Get IDs without committing
        
        # Create a test rule
        rule = CheckinRule(
            solo_user_id=user1.user_id,
            rule_name='起床打卡',
            icon_url='🌅',
            frequency_type=0,
            time_slot_type=4,
            custom_time=None,
            week_days=127,
            status=1
        )
        
        test_db.session.add(rule)
        test_db.session.flush()
        
        # Create supervision relation
        relation = SupervisionRuleRelation(
            solo_user_id=user1.user_id,
            supervisor_user_id=user2.user_id,
            rule_id=rule.rule_id,  # Specific rule supervision
            status=1  # Pending
        )
        
        test_db.session.add(relation)
        test_db.session.commit()
        
        # Verify the relation was created
        assert relation.relation_id is not None
        assert relation.solo_user_id == user1.user_id
        assert relation.supervisor_user_id == user2.user_id
        assert relation.rule_id == rule.rule_id
        assert relation.status == 1
        assert relation.created_at is not None
        assert relation.updated_at is not None
        
        # Test status name property
        assert relation.status_name == 'pending'

    def test_supervision_all_rules_relation(self, test_db):
        """Test creating a supervision relation for all rules"""
        # Create test users
        user1 = User(
            wechat_openid='test_openid_3',
            nickname='Test User 3',
            role=1,  # solo user
            status=1
        )
        user2 = User(
            wechat_openid='test_openid_4',
            nickname='Test User 4',
            role=2,  # supervisor
            status=1
        )
        
        test_db.session.add(user1)
        test_db.session.add(user2)
        test_db.session.flush()
        
        # Create supervision relation for all rules (rule_id is None)
        relation = SupervisionRuleRelation(
            solo_user_id=user1.user_id,
            supervisor_user_id=user2.user_id,
            rule_id=None,  # All rules supervision
            status=2  # Approved
        )
        
        test_db.session.add(relation)
        test_db.session.commit()
        
        # Verify the relation was created
        assert relation.relation_id is not None
        assert relation.solo_user_id == user1.user_id
        assert relation.supervisor_user_id == user2.user_id
        assert relation.rule_id is None
        assert relation.status == 2
        
        # Test status name property
        assert relation.status_name == 'approved'

    def test_user_supervision_methods(self, test_db):
        """Test the supervision-related methods added to User model"""
        # Create test users
        user1 = User(
            wechat_openid='test_openid_5',
            nickname='Test User 5',
            role=1,  # solo user
            status=1
        )
        user2 = User(
            wechat_openid='test_openid_6',
            nickname='Test User 6',
            role=2,  # supervisor
            status=1
        )
        
        test_db.session.add(user1)
        test_db.session.add(user2)
        test_db.session.flush()
        
        # Create a test rule
        rule = CheckinRule(
            solo_user_id=user1.user_id,
            rule_name='起床打卡',
            icon_url='🌅',
            frequency_type=0,
            time_slot_type=4,
            custom_time=None,
            week_days=127,
            status=1
        )
        
        test_db.session.add(rule)
        test_db.session.flush()
        
        # Create supervision relation
        relation = SupervisionRuleRelation(
            solo_user_id=user1.user_id,
            supervisor_user_id=user2.user_id,
            rule_id=rule.rule_id,
            status=2  # Approved
        )
        
        test_db.session.add(relation)
        test_db.session.commit()
        
        # Test can_supervise_user method
        can_supervise = user2.can_supervise_user(user1.user_id)
        assert can_supervise is True
        
        # Test can_supervise_rule method
        can_supervise_rule = user2.can_supervise_rule(rule.rule_id)
        assert can_supervise_rule is True
        
        # Test get_supervised_users method
        supervised_users = user2.get_supervised_users()
        assert len(supervised_users) == 1
        assert supervised_users[0].user_id == user1.user_id
        
        # Test get_supervised_rules method
        supervised_rules = user2.get_supervised_rules(user1.user_id)
        assert len(supervised_rules) == 1
        assert supervised_rules[0].rule_id == rule.rule_id