"""
GetUserByOpenIdUseCase单元测试
"""
import pytest
from unittest.mock import Mock, patch
from app.application.use_cases.supervision.get_user_by_openid_use_case import GetUserByOpenIdUseCase
from app.application.use_cases.base import UseCaseStatus


class TestGetUserByOpenIdUseCase:
    """测试GetUserByOpenIdUseCase"""

    @patch('app.application.use_cases.supervision.get_user_by_openid_use_case.RepositoryFactory')
    def test_should_successfully_get_user_by_openid(self, mock_repo_factory):
        """应该成功通过OpenID获取用户"""
        # Arrange - 准备测试数据和Mock
        mock_user_repo = Mock()
        mock_repo_factory.get_user_repository.return_value = mock_user_repo

        user = Mock()
        user.user_id = 1
        user.nickname = 'TestUser'
        user.wechat_openid = 'openid123456'

        mock_user_repo.find_by_openid.return_value = user

        use_case = GetUserByOpenIdUseCase()

        # Act - 执行被测试的方法
        result = use_case.execute(openid='openid123456')

        # Assert - 验证行为
        assert result.is_success
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data.user_id == 1
        assert result.data.wechat_openid == 'openid123456'
        mock_user_repo.find_by_openid.assert_called_once_with('openid123456')

    @patch('app.application.use_cases.supervision.get_user_by_openid_use_case.RepositoryFactory')
    def test_should_fail_when_user_not_found(self, mock_repo_factory):
        """应该在用户不存在时失败"""
        # Arrange
        mock_user_repo = Mock()
        mock_repo_factory.get_user_repository.return_value = mock_user_repo
        mock_user_repo.find_by_openid.return_value = None

        use_case = GetUserByOpenIdUseCase()

        # Act
        result = use_case.execute(openid='nonexistent_openid')

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.NOT_FOUND
        assert '用户不存在' in result.message

    @patch('app.application.use_cases.supervision.get_user_by_openid_use_case.RepositoryFactory')
    def test_should_fail_when_openid_is_empty(self, mock_repo_factory):
        """应该在OpenID为空时失败"""
        # Arrange
        use_case = GetUserByOpenIdUseCase()

        # Act
        result = use_case.execute(openid=None)

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert 'OpenID不能为空' in result.message

    @patch('app.application.use_cases.supervision.get_user_by_openid_use_case.RepositoryFactory')
    def test_should_fail_when_openid_is_empty_string(self, mock_repo_factory):
        """应该在OpenID为空字符串时失败"""
        # Arrange
        use_case = GetUserByOpenIdUseCase()

        # Act
        result = use_case.execute(openid='')

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert 'OpenID不能为空' in result.message

    @patch('app.application.use_cases.supervision.get_user_by_openid_use_case.RepositoryFactory')
    def test_should_handle_repository_exception(self, mock_repo_factory):
        """应该处理Repository异常"""
        # Arrange
        mock_user_repo = Mock()
        mock_repo_factory.get_user_repository.return_value = mock_user_repo
        mock_user_repo.find_by_openid.side_effect = Exception('Database error')

        use_case = GetUserByOpenIdUseCase()

        # Act
        result = use_case.execute(openid='openid123456')

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.FAILURE
        assert '查询失败' in result.message