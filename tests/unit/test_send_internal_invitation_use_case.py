"""
Test cases for SendInternalInvitationUseCase
测试站内邀请监督者用例
"""
import pytest
import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from database.flask_models import User, CheckinRule, SupervisionRuleRelation, Community
from test_data_generator import generate_unique_phone_number, generate_unique_openid, generate_unique_nickname
from app.application.use_cases.supervision import SendInternalInvitationUseCase


class TestSendInternalInvitationUseCase:
    """Test cases for SendInternalInvitationUseCase"""

    def test_send_internal_invitation_success(self, test_session):
        """Test successful internal invitation sending"""
        test_context = "test_send_internal_invitation_success"

        # Create test users
        phone_number_1 = generate_unique_phone_number(f"{test_context}_sender")
        openid_1 = generate_unique_openid(phone_number_1, f"{test_context}_sender")
        sender = User(
            wechat_openid=openid_1,
            nickname=generate_unique_nickname(f"{test_context}_sender"),
            phone_number=phone_number_1,
            role=1,
            status=1
        )

        phone_number_2 = generate_unique_phone_number(f"{test_context}_receiver1")
        openid_2 = generate_unique_openid(phone_number_2, f"{test_context}_receiver1")
        receiver1 = User(
            wechat_openid=openid_2,
            nickname=generate_unique_nickname(f"{test_context}_receiver1"),
            phone_number=phone_number_2,
            role=1,
            status=1
        )

        phone_number_3 = generate_unique_phone_number(f"{test_context}_receiver2")
        openid_3 = generate_unique_openid(phone_number_3, f"{test_context}_receiver2")
        receiver2 = User(
            wechat_openid=openid_3,
            nickname=generate_unique_nickname(f"{test_context}_receiver2"),
            phone_number=phone_number_3,
            role=1,
            status=1
        )

        test_session.add(sender)
        test_session.add(receiver1)
        test_session.add(receiver2)
        test_session.flush()

        # Create test community
        community = Community(
            name=f"{test_context}_测试社区",
            status=1
        )
        test_session.add(community)
        test_session.flush()

        # Create a test rule owned by sender
        rule = CheckinRule(
            user_id=sender.user_id,
            community_id=community.community_id,
            rule_type='personal',
            rule_name='每日运动',
            status=1
        )

        test_session.add(rule)
        test_session.flush()

        # Execute use case
        use_case = SendInternalInvitationUseCase()
        result = use_case.execute(
            sender_id=sender.user_id,
            rule_id=rule.rule_id,
            receiver_ids=[receiver1.user_id, receiver2.user_id],
            message="希望你能监督我的每日运动打卡"
        )

        # Verify result
        assert result.is_success
        assert result.status.value == "success"
        assert result.message == "邀请已发送"
        assert result.data is not None
        assert result.data['sender_id'] == sender.user_id
        assert result.data['rule_id'] == rule.rule_id
        assert len(result.data['relation_ids']) == 2
        assert result.data['invitation_type'] == 'internal'
        assert result.data['status'] == 1
        assert 'expires_at' in result.data

        # Verify supervision relations were created
        relations = test_session.query(SupervisionRuleRelation).filter(
            SupervisionRuleRelation.rule_id == rule.rule_id,
            SupervisionRuleRelation.invitation_type == 'internal'
        ).all()

        assert len(relations) == 2
        for relation in relations:
            assert relation.solo_user_id == sender.user_id
            assert relation.status == 1  # Pending
            assert relation.invitation_type == 'internal'
            assert relation.message == "希望你能监督我的每日运动打卡"
            assert relation.invite_expires_at is not None

    def test_send_internal_invitation_max_3_receivers(self, test_session):
        """Test that invitation fails when more than 3 receivers are provided"""
        test_context = "test_send_internal_invitation_max_3_receivers"

        # Create sender
        phone_number_1 = generate_unique_phone_number(f"{test_context}_sender")
        openid_1 = generate_unique_openid(phone_number_1, f"{test_context}_sender")
        sender = User(
            wechat_openid=openid_1,
            nickname=generate_unique_nickname(f"{test_context}_sender"),
            phone_number=phone_number_1,
            role=1,
            status=1
        )

        # Create 4 receivers
        receiver_ids = []
        for i in range(1, 5):
            phone_number = generate_unique_phone_number(f"{test_context}_receiver{i}")
            openid = generate_unique_openid(phone_number, f"{test_context}_receiver{i}")
            receiver = User(
                wechat_openid=openid,
                nickname=generate_unique_nickname(f"{test_context}_receiver{i}"),
                phone_number=phone_number,
                role=1,
                status=1
            )
            test_session.add(receiver)
            receiver_ids.append(receiver.user_id)

        test_session.add(sender)
        test_session.flush()

        # Create test community
        community = Community(
            name=f"{test_context}_测试社区",
            status=1
        )
        test_session.add(community)
        test_session.flush()

        # Create a test rule
        rule = CheckinRule(
            user_id=sender.user_id,
            community_id=community.community_id,
            rule_type='personal',
            rule_name='每日运动',
            status=1
        )

        test_session.add(rule)
        test_session.flush()

        # Execute use case with 4 receivers (should fail)
        use_case = SendInternalInvitationUseCase()
        result = use_case.execute(
            sender_id=sender.user_id,
            rule_id=rule.rule_id,
            receiver_ids=receiver_ids
        )

        # Verify validation error
        assert not result.is_success
        assert result.status.value == "validation_error"
        assert "一次最多只能邀请3个用户" in result.message

    def test_send_internal_invitation_cannot_invite_self(self, test_session):
        """Test that user cannot invite themselves"""
        test_context = "test_send_internal_invitation_cannot_invite_self"

        # Create sender
        phone_number_1 = generate_unique_phone_number(f"{test_context}_sender")
        openid_1 = generate_unique_openid(phone_number_1, f"{test_context}_sender")
        sender = User(
            wechat_openid=openid_1,
            nickname=generate_unique_nickname(f"{test_context}_sender"),
            phone_number=phone_number_1,
            role=1,
            status=1
        )

        test_session.add(sender)
        test_session.flush()

        # Create test community
        community = Community(
            name=f"{test_context}_测试社区",
            status=1
        )
        test_session.add(community)
        test_session.flush()

        # Create a test rule
        rule = CheckinRule(
            user_id=sender.user_id,
            community_id=community.community_id,
            rule_type='personal',
            rule_name='每日运动',
            status=1
        )

        test_session.add(rule)
        test_session.flush()

        # Execute use case with sender in receiver_ids (should fail)
        use_case = SendInternalInvitationUseCase()
        result = use_case.execute(
            sender_id=sender.user_id,
            rule_id=rule.rule_id,
            receiver_ids=[sender.user_id]  # Trying to invite self
        )

        # Verify validation error
        assert not result.is_success
        assert result.status.value == "validation_error"
        assert "不能邀请自己" in result.message

    def test_send_internal_invitation_not_rule_owner(self, test_session):
        """Test that non-owner cannot send invitation for a rule"""
        test_context = "test_send_internal_invitation_not_rule_owner"

        # Create users
        phone_number_1 = generate_unique_phone_number(f"{test_context}_owner")
        openid_1 = generate_unique_openid(phone_number_1, f"{test_context}_owner")
        owner = User(
            wechat_openid=openid_1,
            nickname=generate_unique_nickname(f"{test_context}_owner"),
            phone_number=phone_number_1,
            role=1,
            status=1
        )

        phone_number_2 = generate_unique_phone_number(f"{test_context}_sender")
        openid_2 = generate_unique_openid(phone_number_2, f"{test_context}_sender")
        sender = User(
            wechat_openid=openid_2,
            nickname=generate_unique_nickname(f"{test_context}_sender"),
            phone_number=phone_number_2,
            role=1,
            status=1
        )

        phone_number_3 = generate_unique_phone_number(f"{test_context}_receiver")
        openid_3 = generate_unique_openid(phone_number_3, f"{test_context}_receiver")
        receiver = User(
            wechat_openid=openid_3,
            nickname=generate_unique_nickname(f"{test_context}_receiver"),
            phone_number=phone_number_3,
            role=1,
            status=1
        )

        test_session.add(owner)
        test_session.add(sender)
        test_session.add(receiver)
        test_session.flush()

        # Create test community
        community = Community(
            name=f"{test_context}_测试社区",
            status=1
        )
        test_session.add(community)
        test_session.flush()

        # Create a test rule owned by owner, not sender
        rule = CheckinRule(
            user_id=owner.user_id,  # Owned by owner
            community_id=community.community_id,
            rule_type='personal',
            rule_name='每日运动',
            status=1
        )

        test_session.add(rule)
        test_session.flush()

        # Execute use case with sender trying to invite for owner's rule (should fail)
        use_case = SendInternalInvitationUseCase()
        result = use_case.execute(
            sender_id=sender.user_id,  # Not the owner
            rule_id=rule.rule_id,
            receiver_ids=[receiver.user_id]
        )

        # Verify forbidden error
        assert not result.is_success
        assert result.status.value == "forbidden"
        assert "您不是该规则的所有者" in result.message

    def test_send_internal_invitation_skip_existing_invitation(self, test_session):
        """Test that existing invitations are skipped"""
        test_context = "test_send_internal_invitation_skip_existing"

        # Create users
        phone_number_1 = generate_unique_phone_number(f"{test_context}_sender")
        openid_1 = generate_unique_openid(phone_number_1, f"{test_context}_sender")
        sender = User(
            wechat_openid=openid_1,
            nickname=generate_unique_nickname(f"{test_context}_sender"),
            phone_number=phone_number_1,
            role=1,
            status=1
        )

        phone_number_2 = generate_unique_phone_number(f"{test_context}_receiver1")
        openid_2 = generate_unique_openid(phone_number_2, f"{test_context}_receiver1")
        receiver1 = User(
            wechat_openid=openid_2,
            nickname=generate_unique_nickname(f"{test_context}_receiver1"),
            phone_number=phone_number_2,
            role=1,
            status=1
        )

        phone_number_3 = generate_unique_phone_number(f"{test_context}_receiver2")
        openid_3 = generate_unique_openid(phone_number_3, f"{test_context}_receiver2")
        receiver2 = User(
            wechat_openid=openid_3,
            nickname=generate_unique_nickname(f"{test_context}_receiver2"),
            phone_number=phone_number_3,
            role=1,
            status=1
        )

        test_session.add(sender)
        test_session.add(receiver1)
        test_session.add(receiver2)
        test_session.flush()

        # Create test community
        community = Community(
            name=f"{test_context}_测试社区",
            status=1
        )
        test_session.add(community)
        test_session.flush()

        # Create a test rule
        rule = CheckinRule(
            user_id=sender.user_id,
            community_id=community.community_id,
            rule_type='personal',
            rule_name='每日运动',
            status=1
        )

        test_session.add(rule)
        test_session.flush()

        # Create existing invitation for receiver1
        existing_relation = SupervisionRuleRelation(
            solo_user_id=sender.user_id,
            supervisor_user_id=receiver1.user_id,
            rule_id=rule.rule_id,
            status=1,
            invitation_type='internal'
        )
        test_session.add(existing_relation)
        test_session.flush()

        # Execute use case
        use_case = SendInternalInvitationUseCase()
        result = use_case.execute(
            sender_id=sender.user_id,
            rule_id=rule.rule_id,
            receiver_ids=[receiver1.user_id, receiver2.user_id]
        )

        # Verify success - only one new relation should be created
        assert result.is_success
        assert len(result.data['relation_ids']) == 1  # Only receiver2, receiver1 was skipped

        # Verify only one new relation exists
        relations = test_session.query(SupervisionRuleRelation).filter(
            SupervisionRuleRelation.rule_id == rule.rule_id
        ).all()

        assert len(relations) == 2  # Existing + new one
