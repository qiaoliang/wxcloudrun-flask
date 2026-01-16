"""
CheckExpiredInvitationsUseCase单元测试
"""
import pytest
from unittest.mock import Mock, patch
from app.application.use_cases.background_task import CheckExpiredInvitationsUseCase
from app.application.use_cases.base import UseCaseStatus


class TestCheckExpiredInvitationsUseCase:
    """测试CheckExpiredInvitationsUseCase"""

    @patch('app.application.use_cases.background_task.check_expired_invitations_use_case.RepositoryFactory')
    def test_execute_success_no_expired(self, mock_repo_factory):
        """测试执行成功 - 没有过期邀请"""
        # Arrange
        mock_supervision_repo = Mock()
        mock_repo_factory.get_supervision_relation_repository.return_value = mock_supervision_repo

        # Mock返回空列表
        mock_supervision_repo.find_expired_invitations.return_value = []

        use_case = CheckExpiredInvitationsUseCase()

        # Act
        result = use_case.execute()

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.message == '邀请过期检查完成'
        assert result.data['updated_count'] == 0
        assert result.data['expired_count'] == 0
        mock_supervision_repo.batch_update_status.assert_not_called()

    @patch('app.application.use_cases.background_task.check_expired_invitations_use_case.RepositoryFactory')
    def test_execute_success_with_expired(self, mock_repo_factory):
        """测试执行成功 - 有过期邀请"""
        # Arrange
        mock_supervision_repo = Mock()
        mock_repo_factory.get_supervision_relation_repository.return_value = mock_supervision_repo

        # Mock返回过期邀请
        inv1 = Mock()
        inv1.relation_id = 1
        inv2 = Mock()
        inv2.relation_id = 2

        mock_supervision_repo.find_expired_invitations.return_value = [inv1, inv2]
        mock_supervision_repo.batch_update_status.return_value = 2

        use_case = CheckExpiredInvitationsUseCase()

        # Act
        result = use_case.execute()

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.message == '邀请过期检查完成'
        assert result.data['updated_count'] == 2
        assert result.data['expired_count'] == 2
        mock_supervision_repo.batch_update_status.assert_called_once_with([1, 2], 4)

    @patch('app.application.use_cases.background_task.check_expired_invitations_use_case.RepositoryFactory')
    def test_execute_error(self, mock_repo_factory):
        """测试执行失败"""
        # Arrange
        mock_supervision_repo = Mock()
        mock_repo_factory.get_supervision_relation_repository.return_value = mock_supervision_repo
        mock_supervision_repo.find_expired_invitations.side_effect = Exception("Database error")

        use_case = CheckExpiredInvitationsUseCase()

        # Act
        result = use_case.execute()

        # Assert
        assert result.status == UseCaseStatus.FAILURE
        assert 'Database error' in result.message