"""
Test cases for InvitationManagementUseCase.get_sent_invitations
测试获取发起的邀请列表用例（作为被监督人）
"""
import pytest
import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from database.flask_models import User, CheckinRule, SupervisionRuleRelation, Community
from test_data_generator import generate_unique_phone_number, generate_unique_openid, generate_unique_nickname
from app.application.use_cases.supervision.invitation_management_use_case import InvitationManagementUseCase


class TestGetSentInvitationsUseCase:
    """Test cases for get_sent_invitations method"""

    def test_get_sent_invitations_success(self, test_session):
        """Test successful retrieval of sent invitations"""
        test_context = "test_get_sent_invitations_success"

        # Create test users
        phone_number_1 = generate_unique_phone_number(f"{test_context}_solo_user")
        openid_1 = generate_unique_openid(phone_number_1, f"{test_context}_solo_user")
        solo_user = User(
            wechat_openid=openid_1,
            nickname=generate_unique_nickname(f"{test_context}_solo_user"),
            phone_number=phone_number_1,
            role=1,
            status=1
        )

        phone_number_2 = generate_unique_phone_number(f"{test_context}_supervisor1")
        openid_2 = generate_unique_openid(phone_number_2, f"{test_context}_supervisor1")
        supervisor1 = User(
            wechat_openid=openid_2,
            nickname=generate_unique_nickname(f"{test_context}_supervisor1"),
            phone_number=phone_number_2,
            role=1,
            status=1
        )

        phone_number_3 = generate_unique_phone_number(f"{test_context}_supervisor2")
        openid_3 = generate_unique_openid(phone_number_3, f"{test_context}_supervisor2")
        supervisor2 = User(
            wechat_openid=openid_3,
            nickname=generate_unique_nickname(f"{test_context}_supervisor2"),
            phone_number=phone_number_3,
            role=1,
            status=1
        )

        test_session.add(solo_user)
        test_session.add(supervisor1)
        test_session.add(supervisor2)
        test_session.flush()

        # Create checkin rule for solo_user
        rule = CheckinRule(
            user_id=solo_user.user_id,
            rule_name="晚上吃药",
            frequency_type=0,
            status=1
        )
        test_session.add(rule)
        test_session.flush()

        # Create supervision relations (solo_user invites supervisors)
        expires_at = datetime.now() + timedelta(days=30)

        relation1 = SupervisionRuleRelation(
            solo_user_id=solo_user.user_id,
            supervisor_user_id=supervisor1.user_id,
            rule_id=rule.rule_id,
            status=1,  # Pending
            invitation_type='internal',
            message="请监督我",
            invite_expires_at=expires_at
        )

        relation2 = SupervisionRuleRelation(
            solo_user_id=solo_user.user_id,
            supervisor_user_id=supervisor2.user_id,
            rule_id=rule.rule_id,
            status=2,  # Accepted
            invitation_type='internal',
            message="请监督我2",
            invite_expires_at=expires_at
        )

        test_session.add(relation1)
        test_session.add(relation2)
        test_session.commit()

        # Execute use case (get all invitations, not just pending)
        use_case = InvitationManagementUseCase()
        result = use_case.get_sent_invitations(
            user_id=solo_user.user_id,
            page=1,
            limit=10
        )

        # Assertions
        assert result.is_success, f"Expected success but got: {result.message}"
        assert result.data is not None, "Expected data to be returned"

        invitations = result.data.get('invitations', [])
        total = result.data.get('total', 0)

        # Should return 2 invitations (both sent by solo_user)
        assert len(invitations) == 2, f"Expected 2 invitations, got {len(invitations)}"
        assert total == 2, f"Expected total=2, got {total}"

        # Verify invitations contain both statuses
        statuses = [inv['status'] for inv in invitations]
        assert 1 in statuses, "Expected to find status=1 (pending)"
        assert 2 in statuses, "Expected to find status=2 (accepted)"

        # Verify first invitation details
        inv1 = invitations[0]
        assert 'rule_info' in inv1, "Expected rule_info in invitation"
        assert 'invitee_info' in inv1, "Expected invitee_info in invitation"
        assert inv1['rule_info']['rule_id'] == rule.rule_id

        # Verify second invitation details
        inv2 = invitations[1]
        assert 'rule_info' in inv2, "Expected rule_info in invitation"
        assert 'invitee_info' in inv2, "Expected invitee_info in invitation"
        assert inv2['rule_info']['rule_id'] == rule.rule_id

    def test_get_sent_invitations_empty(self, test_session):
        """Test retrieval when no invitations sent"""
        test_context = "test_get_sent_invitations_empty"

        # Create test user
        phone_number = generate_unique_phone_number(f"{test_context}_user")
        openid = generate_unique_openid(phone_number, f"{test_context}_user")
        user = User(
            wechat_openid=openid,
            nickname=generate_unique_nickname(f"{test_context}_user"),
            phone_number=phone_number,
            role=1,
            status=1
        )

        test_session.add(user)
        test_session.flush()

        # Execute use case
        use_case = InvitationManagementUseCase()
        result = use_case.get_sent_invitations(
            user_id=user.user_id,
            page=1,
            limit=10,
            status=None
        )

        # Assertions
        assert result.is_success
        assert result.data is not None

        invitations = result.data.get('invitations', [])
        total = result.data.get('total', 0)

        assert len(invitations) == 0, "Expected no invitations"
        assert total == 0, "Expected total=0"

    def test_get_sent_invitations_with_status_filter(self, test_session):
        """Test retrieval with status filter"""
        test_context = "test_get_sent_invitations_with_status_filter"

        # Create test users
        phone_number_1 = generate_unique_phone_number(f"{test_context}_solo_user")
        openid_1 = generate_unique_openid(phone_number_1, f"{test_context}_solo_user")
        solo_user = User(
            wechat_openid=openid_1,
            nickname=generate_unique_nickname(f"{test_context}_solo_user"),
            phone_number=phone_number_1,
            role=1,
            status=1
        )

        phone_number_2 = generate_unique_phone_number(f"{test_context}_supervisor1")
        openid_2 = generate_unique_openid(phone_number_2, f"{test_context}_supervisor1")
        supervisor1 = User(
            wechat_openid=openid_2,
            nickname=generate_unique_nickname(f"{test_context}_supervisor1"),
            phone_number=phone_number_2,
            role=1,
            status=1
        )

        phone_number_3 = generate_unique_phone_number(f"{test_context}_supervisor2")
        openid_3 = generate_unique_openid(phone_number_3, f"{test_context}_supervisor2")
        supervisor2 = User(
            wechat_openid=openid_3,
            nickname=generate_unique_nickname(f"{test_context}_supervisor2"),
            phone_number=phone_number_3,
            role=1,
            status=1
        )

        test_session.add(solo_user)
        test_session.add(supervisor1)
        test_session.add(supervisor2)
        test_session.flush()

        # Create checkin rule
        rule = CheckinRule(
            user_id=solo_user.user_id,
            rule_name="晚上吃药",
            frequency_type=0,
            status=1
        )
        test_session.add(rule)
        test_session.flush()

        # Create supervision relations with different statuses
        expires_at = datetime.now() + timedelta(days=30)

        relation1 = SupervisionRuleRelation(
            solo_user_id=solo_user.user_id,
            supervisor_user_id=supervisor1.user_id,
            rule_id=rule.rule_id,
            status=1,  # Pending
            invitation_type='internal',
            invite_expires_at=expires_at
        )

        relation2 = SupervisionRuleRelation(
            solo_user_id=solo_user.user_id,
            supervisor_user_id=supervisor2.user_id,
            rule_id=rule.rule_id,
            status=2,  # Accepted
            invitation_type='internal',
            invite_expires_at=expires_at
        )

        test_session.add(relation1)
        test_session.add(relation2)
        test_session.commit()

        # Execute use case with status filter (only pending)
        use_case = InvitationManagementUseCase()
        result = use_case.get_sent_invitations(
            user_id=solo_user.user_id,
            page=1,
            limit=10,
            status=1  # Only pending
        )

        # Assertions
        assert result.is_success
        invitations = result.data.get('invitations', [])

        # Should only return pending invitations
        assert len(invitations) == 1, f"Expected 1 pending invitation, got {len(invitations)}"
        assert invitations[0]['status'] == 1
