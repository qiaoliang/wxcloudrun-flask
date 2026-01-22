"""
GetPendingInvitationsCountUseCase单元测试
测试获取待处理邀请数量的业务逻辑
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from app.application.use_cases.supervision.get_pending_invitations_count_use_case import GetPendingInvitationsCountUseCase
from app.application.use_cases.base import UseCaseStatus


class TestGetPendingInvitationsCountUseCase:
    """测试GetPendingInvitationsCountUseCase"""

    @patch('app.application.use_cases.supervision.get_pending_invitations_count_use_case.RepositoryFactory')
    def test_should_successfully_count_pending_invitations(self, mock_repo_factory):
        """应该成功统计待处理邀请数量"""
        # Arrange
        mock_relation_repo = Mock()
        mock_rule_repo = Mock()

        mock_repo_factory.get_supervision_relation_repository.return_value = mock_relation_repo
        mock_repo_factory.get_checkin_rule_repository.return_value = mock_rule_repo

        # 创建3个邀请（2个待处理，1个已接受）
        invitation1 = Mock()
        invitation1.relation_id = 1
        invitation1.supervisor_user_id = 1  # 当前用户
        invitation1.solo_user_id = 2
        invitation1.rule_id = 101
        invitation1.status = 1  # 待处理
        invitation1.invite_expires_at = datetime.now() + timedelta(days=7)

        invitation2 = Mock()
        invitation2.relation_id = 2
        invitation2.supervisor_user_id = 1
        invitation2.solo_user_id = 3
        invitation2.rule_id = 102
        invitation2.status = 1  # 待处理
        invitation2.invite_expires_at = datetime.now() + timedelta(days=7)

        invitation3 = Mock()
        invitation3.relation_id = 3
        invitation3.supervisor_user_id = 1
        invitation3.solo_user_id = 4
        invitation3.rule_id = 103
        invitation3.status = 2  # 已接受
        invitation3.invite_expires_at = datetime.now() + timedelta(days=7)

        mock_relation_repo.find_by_supervisor_id.return_value = [
            invitation1, invitation2, invitation3
        ]

        # 创建规则（都是活跃的）
        rule1 = Mock()
        rule1.rule_id = 101
        rule1.status = 1  # 启用
        rule1.deleted_at = None

        rule2 = Mock()
        rule2.rule_id = 102
        rule2.status = 1  # 启用
        rule2.deleted_at = None

        rule3 = Mock()
        rule3.rule_id = 103
        rule3.status = 1  # 启用
        rule3.deleted_at = None

        mock_rule_repo.find_by_id.side_effect = lambda id: {
            101: rule1, 102: rule2, 103: rule3
        }.get(id)

        use_case = GetPendingInvitationsCountUseCase()

        # Act
        result = use_case.execute(user_id=1)

        # Assert
        assert result.is_success
        assert result.data['pending_count'] == 2  # 只有2个待处理的邀请

    @patch('app.application.use_cases.supervision.get_pending_invitations_count_use_case.RepositoryFactory')
    def test_should_exclude_expired_invitations(self, mock_repo_factory):
        """应该排除已过期的邀请"""
        # Arrange
        mock_relation_repo = Mock()
        mock_rule_repo = Mock()

        mock_repo_factory.get_supervision_relation_repository.return_value = mock_relation_repo
        mock_repo_factory.get_checkin_rule_repository.return_value = mock_rule_repo

        # 创建2个邀请（1个待处理，1个已过期）
        invitation1 = Mock()
        invitation1.relation_id = 1
        invitation1.supervisor_user_id = 1
        invitation1.solo_user_id = 2
        invitation1.rule_id = 101
        invitation1.status = 1  # 待处理
        invitation1.invite_expires_at = datetime.now() + timedelta(days=7)

        invitation2 = Mock()
        invitation2.relation_id = 2
        invitation2.supervisor_user_id = 1
        invitation2.solo_user_id = 3
        invitation2.rule_id = 102
        invitation2.status = 1  # 待处理
        invitation2.invite_expires_at = datetime.now() - timedelta(days=1)  # 已过期

        mock_relation_repo.find_by_supervisor_id.return_value = [
            invitation1, invitation2
        ]

        rule1 = Mock()
        rule1.rule_id = 101
        rule1.status = 1
        rule1.deleted_at = None

        rule2 = Mock()
        rule2.rule_id = 102
        rule2.status = 1
        rule2.deleted_at = None

        mock_rule_repo.find_by_id.side_effect = lambda id: {
            101: rule1, 102: rule2
        }.get(id)

        use_case = GetPendingInvitationsCountUseCase()

        # Act
        result = use_case.execute(user_id=1)

        # Assert
        assert result.is_success
        assert result.data['pending_count'] == 1  # 只有1个未过期的邀请

    @patch('app.application.use_cases.supervision.get_pending_invitations_count_use_case.RepositoryFactory')
    def test_should_exclude_inactive_rules(self, mock_repo_factory):
        """应该排除已停用的规则"""
        # Arrange
        mock_relation_repo = Mock()
        mock_rule_repo = Mock()

        mock_repo_factory.get_supervision_relation_repository.return_value = mock_relation_repo
        mock_repo_factory.get_checkin_rule_repository.return_value = mock_rule_repo

        # 创建2个邀请（1个规则启用，1个规则停用）
        invitation1 = Mock()
        invitation1.relation_id = 1
        invitation1.supervisor_user_id = 1
        invitation1.solo_user_id = 2
        invitation1.rule_id = 101
        invitation1.status = 1
        invitation1.invite_expires_at = datetime.now() + timedelta(days=7)

        invitation2 = Mock()
        invitation2.relation_id = 2
        invitation2.supervisor_user_id = 1
        invitation2.solo_user_id = 3
        invitation2.rule_id = 102
        invitation2.status = 1
        invitation2.invite_expires_at = datetime.now() + timedelta(days=7)

        mock_relation_repo.find_by_supervisor_id.return_value = [
            invitation1, invitation2
        ]

        rule1 = Mock()
        rule1.rule_id = 101
        rule1.status = 1  # 启用
        rule1.deleted_at = None

        rule2 = Mock()
        rule2.rule_id = 102
        rule2.status = 0  # 停用
        rule2.deleted_at = None

        mock_rule_repo.find_by_id.side_effect = lambda id: {
            101: rule1, 102: rule2
        }.get(id)

        use_case = GetPendingInvitationsCountUseCase()

        # Act
        result = use_case.execute(user_id=1)

        # Assert
        assert result.is_success
        assert result.data['pending_count'] == 1  # 只有1个规则启用的邀请

    @patch('app.application.use_cases.supervision.get_pending_invitations_count_use_case.RepositoryFactory')
    def test_should_exclude_deleted_rules(self, mock_repo_factory):
        """应该排除已删除的规则"""
        # Arrange
        mock_relation_repo = Mock()
        mock_rule_repo = Mock()

        mock_repo_factory.get_supervision_relation_repository.return_value = mock_relation_repo
        mock_repo_factory.get_checkin_rule_repository.return_value = mock_rule_repo

        # 创建2个邀请（1个规则存在，1个规则已删除）
        invitation1 = Mock()
        invitation1.relation_id = 1
        invitation1.supervisor_user_id = 1
        invitation1.solo_user_id = 2
        invitation1.rule_id = 101
        invitation1.status = 1
        invitation1.invite_expires_at = datetime.now() + timedelta(days=7)

        invitation2 = Mock()
        invitation2.relation_id = 2
        invitation2.supervisor_user_id = 1
        invitation2.solo_user_id = 3
        invitation2.rule_id = 102
        invitation2.status = 1
        invitation2.invite_expires_at = datetime.now() + timedelta(days=7)

        mock_relation_repo.find_by_supervisor_id.return_value = [
            invitation1, invitation2
        ]

        rule1 = Mock()
        rule1.rule_id = 101
        rule1.status = 1
        rule1.deleted_at = None

        # 规则102已删除
        mock_rule_repo.find_by_id.side_effect = lambda id: rule1 if id == 101 else None

        use_case = GetPendingInvitationsCountUseCase()

        # Act
        result = use_case.execute(user_id=1)

        # Assert
        assert result.is_success
        assert result.data['pending_count'] == 1  # 只有1个规则存在的邀请

    @patch('app.application.use_cases.supervision.get_pending_invitations_count_use_case.RepositoryFactory')
    def test_should_return_zero_when_no_pending_invitations(self, mock_repo_factory):
        """应该在无待处理邀请时返回0"""
        # Arrange
        mock_relation_repo = Mock()
        mock_repo_factory.get_supervision_relation_repository.return_value = mock_relation_repo
        mock_relation_repo.find_by_supervisor_id.return_value = []

        use_case = GetPendingInvitationsCountUseCase()

        # Act
        result = use_case.execute(user_id=1)

        # Assert
        assert result.is_success
        assert result.data['pending_count'] == 0

    def test_should_fail_when_user_id_is_empty(self):
        """应该在用户ID为空时失败"""
        # Arrange
        use_case = GetPendingInvitationsCountUseCase()

        # Act
        result = use_case.execute(user_id=None)

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '用户ID不能为空' in result.message