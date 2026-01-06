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
from test_data_generator import generate_unique_phone_number, generate_unique_openid, generate_unique_nickname


class TestSupervisionRuleRelationModel:
    """Test cases for SupervisionRuleRelation model"""

    def test_supervision_rule_relation_creation(self, test_session):
        """Test creating a supervision rule relation"""
        test_context = "test_supervision_rule_relation_creation"

        # Create test users
        phone_number_1 = generate_unique_phone_number(f"{test_context}_user1")
        openid_1 = generate_unique_openid(phone_number_1, f"{test_context}_user1")
        user1 = User(
            wechat_openid=openid_1,
            nickname=generate_unique_nickname(f"{test_context}_user1"),
            phone_number=phone_number_1,
            role=1,  # solo user
            status=1
        )

        phone_number_2 = generate_unique_phone_number(f"{test_context}_user2")
        openid_2 = generate_unique_openid(phone_number_2, f"{test_context}_user2")
        user2 = User(
            wechat_openid=openid_2,
            nickname=generate_unique_nickname(f"{test_context}_user2"),
            phone_number=phone_number_2,
            role=2,  # supervisor
            status=1
        )

        test_session.add(user1)
        test_session.add(user2)
        test_session.flush()  # Get IDs without committing

        # Create test community
        community = Community(
            name=f"{test_context}_测试社区",
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
        test_context = "test_supervision_all_rules_relation"

        # Create test users
        phone_number_3 = generate_unique_phone_number(f"{test_context}_user3")
        openid_3 = generate_unique_openid(phone_number_3, f"{test_context}_user3")
        user1 = User(
            wechat_openid=openid_3,
            nickname=generate_unique_nickname(f"{test_context}_user3"),
            phone_number=phone_number_3,
            role=1,  # solo user
            status=1
        )

        phone_number_4 = generate_unique_phone_number(f"{test_context}_user4")
        openid_4 = generate_unique_openid(phone_number_4, f"{test_context}_user4")
        user2 = User(
            wechat_openid=openid_4,
            nickname=generate_unique_nickname(f"{test_context}_user4"),
            phone_number=phone_number_4,
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
        test_context = "test_supervision_relation_status_update"

        # Create test users and relation
        phone_number_5 = generate_unique_phone_number(f"{test_context}_user5")
        openid_5 = generate_unique_openid(phone_number_5, f"{test_context}_user5")
        user1 = User(
            wechat_openid=openid_5,
            nickname=generate_unique_nickname(f"{test_context}_user5"),
            phone_number=phone_number_5,
            role=1,
            status=1
        )

        phone_number_6 = generate_unique_phone_number(f"{test_context}_user6")
        openid_6 = generate_unique_openid(phone_number_6, f"{test_context}_user6")
        user2 = User(
            wechat_openid=openid_6,
            nickname=generate_unique_nickname(f"{test_context}_user6"),
            phone_number=phone_number_6,
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
        test_context = "test_multiple_supervisors_for_single_user"

        # Create users
        phone_number_solo = generate_unique_phone_number(f"{test_context}_solo")
        openid_solo = generate_unique_openid(phone_number_solo, f"{test_context}_solo")
        solo_user = User(
            wechat_openid=openid_solo,
            nickname=generate_unique_nickname(f"{test_context}_solo"),
            phone_number=phone_number_solo,
            role=1,
            status=1
        )

        phone_number_sup1 = generate_unique_phone_number(f"{test_context}_sup1")
        openid_sup1 = generate_unique_openid(phone_number_sup1, f"{test_context}_sup1")
        supervisor1 = User(
            wechat_openid=openid_sup1,
            nickname=generate_unique_nickname(f"{test_context}_sup1"),
            phone_number=phone_number_sup1,
            role=2,
            status=1
        )

        phone_number_sup2 = generate_unique_phone_number(f"{test_context}_sup2")
        openid_sup2 = generate_unique_openid(phone_number_sup2, f"{test_context}_sup2")
        supervisor2 = User(
            wechat_openid=openid_sup2,
            nickname=generate_unique_nickname(f"{test_context}_sup2"),
            phone_number=phone_number_sup2,
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
        test_context = "test_supervisor_over_multiple_users"

        # Create users
        phone_number_main = generate_unique_phone_number(f"{test_context}_main")
        openid_main = generate_unique_openid(phone_number_main, f"{test_context}_main")
        supervisor = User(
            wechat_openid=openid_main,
            nickname=generate_unique_nickname(f"{test_context}_main"),
            phone_number=phone_number_main,
            role=2,
            status=1
        )

        phone_number_solo1 = generate_unique_phone_number(f"{test_context}_solo1")
        openid_solo1 = generate_unique_openid(phone_number_solo1, f"{test_context}_solo1")
        solo_user1 = User(
            wechat_openid=openid_solo1,
            nickname=generate_unique_nickname(f"{test_context}_solo1"),
            phone_number=phone_number_solo1,
            role=1,
            status=1
        )

        phone_number_solo2 = generate_unique_phone_number(f"{test_context}_solo2")
        openid_solo2 = generate_unique_openid(phone_number_solo2, f"{test_context}_solo2")
        solo_user2 = User(
            wechat_openid=openid_solo2,
            nickname=generate_unique_nickname(f"{test_context}_solo2"),
            phone_number=phone_number_solo2,
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
        test_context = "test_supervision_with_specific_rule"

        # Create users and rule
        phone_number_user = generate_unique_phone_number(f"{test_context}_user")
        openid_user = generate_unique_openid(phone_number_user, f"{test_context}_user")
        user = User(
            wechat_openid=openid_user,
            nickname=generate_unique_nickname(f"{test_context}_user"),
            phone_number=phone_number_user,
            role=1,
            status=1
        )

        phone_number_supervisor = generate_unique_phone_number(f"{test_context}_supervisor")
        openid_supervisor = generate_unique_openid(phone_number_supervisor, f"{test_context}_supervisor")
        supervisor = User(
            wechat_openid=openid_supervisor,
            nickname=generate_unique_nickname(f"{test_context}_supervisor"),
            phone_number=phone_number_supervisor,
            role=2,
            status=1
        )

        test_session.add_all([user, supervisor])
        test_session.flush()

        # Create test community
        community = Community(
            name=f"{test_context}_测试社区",
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
        test_context = "test_supervision_relation_delete"

        # Create user and relation
        phone_number_user = generate_unique_phone_number(f"{test_context}_user")
        openid_user = generate_unique_openid(phone_number_user, f"{test_context}_user")
        user = User(
            wechat_openid=openid_user,
            nickname=generate_unique_nickname(f"{test_context}_user"),
            phone_number=phone_number_user,
            role=1,
            status=1
        )

        phone_number_supervisor = generate_unique_phone_number(f"{test_context}_supervisor")
        openid_supervisor = generate_unique_openid(phone_number_supervisor, f"{test_context}_supervisor")
        supervisor = User(
            wechat_openid=openid_supervisor,
            nickname=generate_unique_nickname(f"{test_context}_supervisor"),
            phone_number=phone_number_supervisor,
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
            wechat_openid=openid_user
        ).first()
        assert remaining_user is not None