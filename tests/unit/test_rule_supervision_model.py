"""
Test cases for SupervisionRuleRelation model and related functionality
使用新的数据库架构
"""
import pytest
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from database.flask_models import User, CheckinRule, SupervisionRuleRelation, Community


class TestSupervisionRuleRelationModel:
    """Test cases for SupervisionRuleRelation model"""

    def test_supervision_rule_relation_creation(self, test_session):
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

        test_session.add(user1)
        test_session.add(user2)
        test_session.flush()  # Get IDs without committing

        # Create test community
        community = Community(
            name="测试社区",
            status=1
        )
        test_session.add(community)
        test_session.flush()

        # Create a test rule
        rule = CheckinRule(
            user_id=user1.user_id,
            community_id=community.community_id,
            rule_type='personal',
            rule_name='起床打卡',
            status=1
        )

        test_session.add(rule)
        test_session.flush()

        # Create supervision relation
        relation = SupervisionRuleRelation(
            solo_user_id=user1.user_id,
            supervisor_user_id=user2.user_id,
            rule_id=rule.rule_id,  # Specific rule supervision
            status=1  # Pending
        )

        test_session.add(relation)
        test_session.commit()

        # Verify the relation was created
        assert relation.relation_id is not None
        assert relation.solo_user_id == user1.user_id
        assert relation.supervisor_user_id == user2.user_id
        assert relation.rule_id == rule.rule_id
        assert relation.status == 1
        assert relation.created_at is not None
        assert relation.updated_at is not None

    def test_supervision_all_rules_relation(self, test_session):
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

        test_session.add(user1)
        test_session.add(user2)
        test_session.flush()

        # Create supervision relation for all rules (rule_id is None)
        relation = SupervisionRuleRelation(
            solo_user_id=user1.user_id,
            supervisor_user_id=user2.user_id,
            rule_id=None,  # All rules supervision
            status=1
        )

        test_session.add(relation)
        test_session.commit()

        # Verify the relation was created
        assert relation.relation_id is not None
        assert relation.solo_user_id == user1.user_id
        assert relation.supervisor_user_id == user2.user_id
        assert relation.rule_id is None  # All rules
        assert relation.status == 1

    def test_supervision_relation_status_update(self, test_session):
        """Test updating supervision relation status"""
        # Create test users and relation
        user1 = User(
            wechat_openid='test_openid_5',
            nickname='Test User 5',
            role=1,
            status=1
        )
        user2 = User(
            wechat_openid='test_openid_6',
            nickname='Test User 6',
            role=2,
            status=1
        )

        test_session.add_all([user1, user2])
        test_session.flush()

        relation = SupervisionRuleRelation(
            solo_user_id=user1.user_id,
            supervisor_user_id=user2.user_id,
            status=1  # Pending
        )
        test_session.add(relation)
        test_session.commit()

        # Update status to active
        relation.status = 2  # Active
        test_session.commit()

        # Verify update
        updated_relation = test_session.query(SupervisionRuleRelation).filter_by(
            relation_id=relation.relation_id
        ).first()
        assert updated_relation.status == 2

    def test_multiple_supervisors_for_single_user(self, test_session):
        """Test a single user having multiple supervisors"""
        # Create users
        solo_user = User(
            wechat_openid='solo_user_multi',
            nickname='Solo User',
            role=1,
            status=1
        )
        supervisor1 = User(
            wechat_openid='supervisor_1',
            nickname='Supervisor 1',
            role=2,
            status=1
        )
        supervisor2 = User(
            wechat_openid='supervisor_2',
            nickname='Supervisor 2',
            role=2,
            status=1
        )

        test_session.add_all([solo_user, supervisor1, supervisor2])
        test_session.flush()

        # Create multiple supervision relations
        relation1 = SupervisionRuleRelation(
            solo_user_id=solo_user.user_id,
            supervisor_user_id=supervisor1.user_id,
            status=1
        )
        relation2 = SupervisionRuleRelation(
            solo_user_id=solo_user.user_id,
            supervisor_user_id=supervisor2.user_id,
            status=1
        )

        test_session.add_all([relation1, relation2])
        test_session.commit()

        # Verify multiple supervisors
        supervisor_relations = test_session.query(SupervisionRuleRelation).filter_by(
            solo_user_id=solo_user.user_id
        ).all()
        assert len(supervisor_relations) == 2

    def test_supervisor_over_multiple_users(self, test_session):
        """Test a supervisor overseeing multiple users"""
        # Create users
        supervisor = User(
            wechat_openid='main_supervisor',
            nickname='Main Supervisor',
            role=2,
            status=1
        )
        solo_user1 = User(
            wechat_openid='solo_user_1',
            nickname='Solo User 1',
            role=1,
            status=1
        )
        solo_user2 = User(
            wechat_openid='solo_user_2',
            nickname='Solo User 2',
            role=1,
            status=1
        )

        test_session.add_all([supervisor, solo_user1, solo_user2])
        test_session.flush()

        # Create supervision relations
        relation1 = SupervisionRuleRelation(
            solo_user_id=solo_user1.user_id,
            supervisor_user_id=supervisor.user_id,
            status=1
        )
        relation2 = SupervisionRuleRelation(
            solo_user_id=solo_user2.user_id,
            supervisor_user_id=supervisor.user_id,
            status=1
        )

        test_session.add_all([relation1, relation2])
        test_session.commit()

        # Verify supervisor oversees multiple users
        supervised_users = test_session.query(SupervisionRuleRelation).filter_by(
            supervisor_user_id=supervisor.user_id
        ).all()
        assert len(supervised_users) == 2

    def test_supervision_with_specific_rule(self, test_session):
        """Test supervision relation tied to specific rule"""
        # Create users and rule
        user = User(
            wechat_openid='rule_test_user',
            nickname='Rule Test User',
            role=1,
            status=1
        )
        supervisor = User(
            wechat_openid='rule_test_supervisor',
            nickname='Rule Test Supervisor',
            role=2,
            status=1
        )

        test_session.add_all([user, supervisor])
        test_session.flush()

        # Create test community
        community = Community(
            name="测试社区",
            status=1
        )
        test_session.add(community)
        test_session.flush()

        rule = CheckinRule(
            user_id=user.user_id,
            community_id=community.community_id,
            rule_type='personal',
            rule_name='早起打卡',
            status=1
        )
        test_session.add(rule)
        test_session.flush()

        # Create supervision for specific rule
        relation = SupervisionRuleRelation(
            solo_user_id=user.user_id,
            supervisor_user_id=supervisor.user_id,
            rule_id=rule.rule_id,
            status=1
        )
        test_session.add(relation)
        test_session.commit()

        # Verify relation is tied to specific rule
        found_relation = test_session.query(SupervisionRuleRelation).filter_by(
            relation_id=relation.relation_id
        ).first()
        assert found_relation.rule_id == rule.rule_id

    def test_supervision_relation_delete(self, test_session):
        """Test delete supervision relation"""
        # Create user and relation
        user = User(
            wechat_openid='delete_test_user',
            nickname='Delete Test User',
            role=1,
            status=1
        )
        supervisor = User(
            wechat_openid='delete_test_supervisor',
            nickname='Delete Test Supervisor',
            role=2,
            status=1
        )

        test_session.add_all([user, supervisor])
        test_session.flush()

        relation = SupervisionRuleRelation(
            solo_user_id=user.user_id,
            supervisor_user_id=supervisor.user_id,
            status=1
        )
        test_session.add(relation)
        test_session.commit()

        relation_id = relation.relation_id

        # Delete the supervision relation
        test_session.delete(relation)
        test_session.commit()

        # Verify relation is deleted
        remaining_relation = test_session.query(SupervisionRuleRelation).filter_by(
            relation_id=relation_id
        ).first()
        assert remaining_relation is None

        # Verify users still exist
        remaining_user = test_session.query(User).filter_by(
            wechat_openid='delete_test_user'
        ).first()
        assert remaining_user is not None