"""
UpdateUserUseCase单元测试
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.application.use_cases.user.update_user_use_case import UpdateUserUseCase
from app.application.use_cases.base import UseCaseStatus


class TestUpdateUserUseCase:
    """测试UpdateUserUseCase"""

    @patch('app.application.use_cases.user.update_user_use_case.RepositoryFactory')
    @patch('app.application.use_cases.user.update_user_use_case.EventBus')
    def test_should_successfully_update_user_nickname(self, mock_event_bus, mock_repo_factory):
        """应该成功更新用户昵称"""
        # Arrange - 准备测试数据和Mock
        mock_user_repo = Mock()
        mock_repo_factory.get_user_repository.return_value = mock_user_repo

        # 创建一个模拟User对象，包含user属性
        existing_user_model = Mock()
        existing_user_model.user_id = 1
        existing_user_model.nickname = 'OldNickname'
        existing_user_model.avatar_url = 'old_avatar.jpg'
        existing_user_model.name = 'OldName'
        existing_user_model.address = 'OldAddress'
        existing_user_model.motto = 'OldMotto'

        existing_user = Mock()
        existing_user.user = existing_user_model

        mock_user_repo.find_by_id.return_value = existing_user_model
        mock_user_repo.save.return_value = existing_user_model

        mock_event_bus_instance = Mock()
        mock_event_bus.return_value = mock_event_bus_instance

        use_case = UpdateUserUseCase()

        # Act - 执行被测试的方法
        user_to_update = Mock()
        user_to_update.user_id = 1
        user_to_update.nickname = 'NewNickname'
        # 确保其他属性为None，避免触发不必要的更新
        user_to_update.avatar_url = None
        user_to_update.name = None
        user_to_update.address = None
        user_to_update.motto = None

        result = use_case.execute(user=user_to_update)

        # Assert - 验证行为
        assert result.is_success
        assert result.status == UseCaseStatus.SUCCESS
        assert '更新用户信息成功' in result.message
        mock_user_repo.find_by_id.assert_called_once_with(1)
        mock_user_repo.save.assert_called_once()
        mock_event_bus_instance.publish.assert_called()  # 验证领域事件被发布

    @patch('app.application.use_cases.user.update_user_use_case.RepositoryFactory')
    @patch('app.application.use_cases.user.update_user_use_case.EventBus')
    def test_should_successfully_update_multiple_fields(self, mock_event_bus, mock_repo_factory):
        """应该成功更新多个用户字段"""
        # Arrange
        mock_user_repo = Mock()
        mock_repo_factory.get_user_repository.return_value = mock_user_repo

        existing_user_model = Mock()
        existing_user_model.user_id = 1
        existing_user_model.nickname = 'OldNickname'
        existing_user_model.avatar_url = 'old.jpg'
        existing_user_model.name = 'OldName'
        existing_user_model.address = 'OldAddress'
        existing_user_model.motto = 'OldMotto'

        existing_user = Mock()
        existing_user.user = existing_user_model

        mock_user_repo.find_by_id.return_value = existing_user_model
        mock_user_repo.save.return_value = existing_user_model

        mock_event_bus_instance = Mock()
        mock_event_bus.return_value = mock_event_bus_instance

        use_case = UpdateUserUseCase()

        # Act
        user_to_update = Mock()
        user_to_update.user_id = 1
        user_to_update.nickname = 'NewNickname'
        user_to_update.avatar_url = 'new.jpg'
        user_to_update.name = 'NewName'
        user_to_update.address = None
        user_to_update.motto = None

        result = use_case.execute(user=user_to_update)

        # Assert
        assert result.is_success
        assert result.status == UseCaseStatus.SUCCESS
        mock_user_repo.save.assert_called_once()

    @patch('app.application.use_cases.user.update_user_use_case.RepositoryFactory')
    def test_should_fail_when_user_not_found(self, mock_repo_factory):
        """应该在用户不存在时失败"""
        # Arrange
        mock_user_repo = Mock()
        mock_repo_factory.get_user_repository.return_value = mock_user_repo
        mock_user_repo.find_by_id.return_value = None

        use_case = UpdateUserUseCase()

        # Act
        user_to_update = Mock()
        user_to_update.user_id = 999

        result = use_case.execute(user=user_to_update)

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.NOT_FOUND
        assert '用户不存在' in result.message

    @patch('app.application.use_cases.user.update_user_use_case.RepositoryFactory')
    def test_should_fail_when_user_is_none(self, mock_repo_factory):
        """应该在用户为None时失败"""
        # Arrange
        use_case = UpdateUserUseCase()

        # Act
        result = use_case.execute(user=None)

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '用户或用户ID不能为空' in result.message

    @patch('app.application.use_cases.user.update_user_use_case.RepositoryFactory')
    def test_should_fail_when_user_id_is_none(self, mock_repo_factory):
        """应该在用户ID为None时失败"""
        # Arrange
        use_case = UpdateUserUseCase()

        # Act
        user_to_update = Mock()
        user_to_update.user_id = None

        result = use_case.execute(user=user_to_update)

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '用户或用户ID不能为空' in result.message

    @patch('app.application.use_cases.user.update_user_use_case.RepositoryFactory')
    @patch('app.application.use_cases.user.update_user_use_case.EventBus')
    def test_should_handle_repository_exception(self, mock_event_bus, mock_repo_factory):
        """应该处理Repository异常"""
        # Arrange
        mock_user_repo = Mock()
        mock_repo_factory.get_user_repository.return_value = mock_user_repo

        existing_user_model = Mock()
        existing_user_model.user_id = 1

        existing_user = Mock()
        existing_user.user = existing_user_model

        mock_user_repo.find_by_id.return_value = existing_user_model
        mock_user_repo.save.side_effect = Exception('Database error')

        mock_event_bus_instance = Mock()
        mock_event_bus.return_value = mock_event_bus_instance

        use_case = UpdateUserUseCase()

        # Act
        user_to_update = Mock()
        user_to_update.user_id = 1
        user_to_update.nickname = 'NewNickname'

        result = use_case.execute(user=user_to_update)

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.FAILURE
        assert '更新用户信息失败' in result.message

    @patch('app.application.use_cases.user.update_user_use_case.RepositoryFactory')
    @patch('app.application.use_cases.user.update_user_use_case.EventBus')
    def test_should_publish_domain_events(self, mock_event_bus, mock_repo_factory):
        """应该发布领域事件"""
        # Arrange
        mock_user_repo = Mock()
        mock_repo_factory.get_user_repository.return_value = mock_user_repo

        existing_user_model = Mock()
        existing_user_model.user_id = 1
        existing_user_model.nickname = 'OldNickname'

        existing_user = Mock()
        existing_user.user = existing_user_model

        mock_user_repo.find_by_id.return_value = existing_user_model
        mock_user_repo.save.return_value = existing_user_model

        mock_event_bus_instance = Mock()
        mock_event_bus.return_value = mock_event_bus_instance

        use_case = UpdateUserUseCase()

        # Act
        user_to_update = Mock()
        user_to_update.user_id = 1
        user_to_update.nickname = 'NewNickname'
        user_to_update.avatar_url = None
        user_to_update.name = None
        user_to_update.address = None
        user_to_update.motto = None

        result = use_case.execute(user=user_to_update)

        # Assert
        assert result.is_success
        mock_event_bus_instance.publish.assert_called()  # 验证领域事件被发布