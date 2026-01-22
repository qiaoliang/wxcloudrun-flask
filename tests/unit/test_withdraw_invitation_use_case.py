"""
WithdrawInvitationUseCase单元测试
测试撤回邀请的业务逻辑
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from app.application.use_cases.supervision.withdraw_invitation_use_case import WithdrawInvitationUseCase
from app.application.use_cases.base import UseCaseStatus


class TestWithdrawInvitationUseCase:
    """测试WithdrawInvitationUseCase"""

    @patch('app.application.use_cases.supervision.withdraw_invitation_use_case.RepositoryFactory')
    def test_should_successfully_withdraw_pending_invitation(self, mock_repo_factory):
        """应该成功撤回待处理的邀请"""
        # Arrange
        mock_user_repo = Mock()
        mock_relation_repo = Mock()

        mock_repo_factory.get_user_repository.return_value = mock_user_repo
        mock_repo_factory.get_supervision_relation_repository.return_value = mock_relation_repo

        # 创建邀请对象（状态为待处理）
        invitation = Mock()
        invitation.relation_id = 123
        invitation.solo_user_id = 1  # 邀请发起者
        invitation.supervisor_user_id = 2  # 被邀请人
        invitation.rule_id = 101
        invitation.status = 1  # 待处理
        invitation.invite_expires_at = datetime.now() + timedelta(days=7)  # 未过期

        mock_relation_repo.find_by_id.return_value = invitation

        use_case = WithdrawInvitationUseCase()

        # Act
        result = use_case.execute(
            invitation_id=123,
            operator_id=1  # 操作者是邀请发起者
        )

        # Assert
        assert result.is_success
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['invitation_id'] == 123
        assert 'withdrawn_at' in result.data
        # 验证状态已更新为已撤回（status=5）
        assert invitation.status == 5
        mock_relation_repo.update.assert_called_once_with(invitation)

    @patch('app.application.use_cases.supervision.withdraw_invitation_use_case.RepositoryFactory')
    def test_should_fail_when_invitation_not_found(self, mock_repo_factory):
        """应该在邀请不存在时失败"""
        # Arrange
        mock_relation_repo = Mock()
        mock_repo_factory.get_supervision_relation_repository.return_value = mock_relation_repo
        mock_relation_repo.find_by_id.return_value = None

        use_case = WithdrawInvitationUseCase()

        # Act
        result = use_case.execute(
            invitation_id=999,
            operator_id=1
        )

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.NOT_FOUND
        assert '邀请不存在' in result.message

    @patch('app.application.use_cases.supervision.withdraw_invitation_use_case.RepositoryFactory')
    def test_should_fail_when_operator_is_not_inviter(self, mock_repo_factory):
        """应该在操作者不是邀请发起者时失败"""
        # Arrange
        mock_relation_repo = Mock()
        mock_repo_factory.get_supervision_relation_repository.return_value = mock_relation_repo

        invitation = Mock()
        invitation.relation_id = 123
        invitation.solo_user_id = 1  # 邀请发起者
        invitation.supervisor_user_id = 2
        invitation.status = 1  # 待处理
        invitation.invite_expires_at = datetime.now() + timedelta(days=7)

        mock_relation_repo.find_by_id.return_value = invitation

        use_case = WithdrawInvitationUseCase()

        # Act
        result = use_case.execute(
            invitation_id=123,
            operator_id=3  # 操作者不是邀请发起者
        )

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.FORBIDDEN
        assert '无权限操作此邀请' in result.message

    @patch('app.application.use_cases.supervision.withdraw_invitation_use_case.RepositoryFactory')
    def test_should_fail_when_invitation_status_not_pending(self, mock_repo_factory):
        """应该在邀请状态不是待处理时失败"""
        # Arrange
        mock_relation_repo = Mock()
        mock_repo_factory.get_supervision_relation_repository.return_value = mock_relation_repo

        invitation = Mock()
        invitation.relation_id = 123
        invitation.solo_user_id = 1
        invitation.supervisor_user_id = 2
        invitation.status = 2  # 已接受
        invitation.invite_expires_at = datetime.now() + timedelta(days=7)

        mock_relation_repo.find_by_id.return_value = invitation

        use_case = WithdrawInvitationUseCase()

        # Act
        result = use_case.execute(
            invitation_id=123,
            operator_id=1
        )

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.BUSINESS_ERROR
        assert '只能撤回待处理的邀请' in result.message

    @patch('app.application.use_cases.supervision.withdraw_invitation_use_case.RepositoryFactory')
    def test_should_fail_when_invitation_expired(self, mock_repo_factory):
        """应该在邀请已过期时失败"""
        # Arrange
        mock_relation_repo = Mock()
        mock_repo_factory.get_supervision_relation_repository.return_value = mock_relation_repo

        invitation = Mock()
        invitation.relation_id = 123
        invitation.solo_user_id = 1
        invitation.supervisor_user_id = 2
        invitation.status = 1  # 待处理
        invitation.invite_expires_at = datetime.now() - timedelta(days=1)  # 已过期

        mock_relation_repo.find_by_id.return_value = invitation

        use_case = WithdrawInvitationUseCase()

        # Act
        result = use_case.execute(
            invitation_id=123,
            operator_id=1
        )

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.BUSINESS_ERROR
        assert '邀请已过期' in result.message

    def test_should_fail_when_invitation_id_is_empty(self):
        """应该在邀请ID为空时失败"""
        # Arrange
        use_case = WithdrawInvitationUseCase()

        # Act
        result = use_case.execute(
            invitation_id=None,
            operator_id=1
        )

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '邀请ID不能为空' in result.message

    def test_should_fail_when_operator_id_is_empty(self):
        """应该在操作者ID为空时失败"""
        # Arrange
        use_case = WithdrawInvitationUseCase()

        # Act
        result = use_case.execute(
            invitation_id=123,
            operator_id=None
        )

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '操作者ID不能为空' in result.message