"""
GetUserByIdUseCase单元测试
"""
import pytest
from unittest.mock import Mock, patch
from app.application.use_cases.supervision.get_user_by_id_use_case import GetUserByIdUseCase
from app.application.use_cases.base import UseCaseStatus


class TestGetUserByIdUseCase:
    """测试GetUserByIdUseCase"""

    @patch('app.application.use_cases.supervision.get_user_by_id_use_case.RepositoryFactory')
    def test_should_successfully_get_user_by_id(self, mock_repo_factory):
        """应该成功通过ID获取用户"""
        # Arrange - 准备测试数据和Mock
        mock_user_repo = Mock()
        mock_repo_factory.get_user_repository.return_value = mock_user_repo

        user = Mock()
        user.user_id = 1
        user.nickname = 'TestUser'
        user.phone_number = '13800138000'

        mock_user_repo.find_by_id.return_value = user

        use_case = GetUserByIdUseCase()

        # Act - 执行被测试的方法
        result = use_case.execute(user_id=1)

        # Assert - 验证行为
        assert result.is_success
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data.user_id == 1
        assert result.data.nickname == 'TestUser'
        mock_user_repo.find_by_id.assert_called_once_with(1)

    @patch('app.application.use_cases.supervision.get_user_by_id_use_case.RepositoryFactory')
    def test_should_fail_when_user_not_found(self, mock_repo_factory):
        """应该在用户不存在时失败"""
        # Arrange
        mock_user_repo = Mock()
        mock_repo_factory.get_user_repository.return_value = mock_user_repo
        mock_user_repo.find_by_id.return_value = None

        use_case = GetUserByIdUseCase()

        # Act
        result = use_case.execute(user_id=999)

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.NOT_FOUND
        assert '用户不存在' in result.message

    @patch('app.application.use_cases.supervision.get_user_by_id_use_case.RepositoryFactory')
    def test_should_fail_when_user_id_is_empty(self, mock_repo_factory):
        """应该在用户ID为空时失败"""
        # Arrange
        use_case = GetUserByIdUseCase()

        # Act
        result = use_case.execute(user_id=None)

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '用户ID不能为空' in result.message

    @patch('app.application.use_cases.supervision.get_user_by_id_use_case.RepositoryFactory')
    def test_should_fail_when_user_id_is_zero(self, mock_repo_factory):
        """应该在用户ID为0时失败"""
        # Arrange
        use_case = GetUserByIdUseCase()

        # Act
        result = use_case.execute(user_id=0)

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '用户ID不能为空' in result.message

    @patch('app.application.use_cases.supervision.get_user_by_id_use_case.RepositoryFactory')
    def test_should_handle_repository_exception(self, mock_repo_factory):
        """应该处理Repository异常"""
        # Arrange
        mock_user_repo = Mock()
        mock_repo_factory.get_user_repository.return_value = mock_user_repo
        mock_user_repo.find_by_id.side_effect = Exception('Database error')

        use_case = GetUserByIdUseCase()

        # Act
        result = use_case.execute(user_id=1)

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.FAILURE
        assert '查询失败' in result.message