"""
AddEventMessageUseCase单元测试
"""
import pytest
from unittest.mock import Mock, patch
from app.application.use_cases.events.add_event_message_use_case import AddEventMessageUseCase
from app.application.use_cases.base import UseCaseStatus


class TestAddEventMessageUseCase:
    """测试AddEventMessageUseCase"""

    @patch('app.application.use_cases.events.add_event_message_use_case.RepositoryFactory')
    @patch('app.application.use_cases.events.add_event_message_use_case.event_bus')
    def test_should_successfully_add_event_message(self, mock_event_bus, mock_repo_factory):
        """应该成功添加事件消息"""
        # Arrange - 准备测试数据和Mock
        mock_user_repo = Mock()
        mock_event_repo = Mock()
        mock_message_repo = Mock()

        mock_repo_factory.get_user_repository.return_value = mock_user_repo
        mock_repo_factory.get_community_event_repository.return_value = mock_event_repo
        mock_repo_factory.get_event_message_repository.return_value = mock_message_repo

        # Mock用户
        user = Mock()
        user.user_id = 1
        mock_user_repo.find_by_id.return_value = user

        # Mock事件
        event = Mock()
        event.event_id = 1
        event.status = 1  # 进行中
        mock_event_repo.find_by_id.return_value = event

        # Mock保存的消息
        saved_message = Mock()
        saved_message.message_id = 1
        mock_message_repo.save.return_value = saved_message

        use_case = AddEventMessageUseCase()

        # Act - 执行被测试的方法
        result = use_case.execute(
            event_id=1,
            user_id=1,
            message='这是一条消息',
            message_type='text'
        )

        # Assert - 验证行为
        assert result.is_success
        assert result.status == UseCaseStatus.SUCCESS
        assert '添加消息成功' in result.message
        assert result.data['message_id'] == 1
        mock_user_repo.find_by_id.assert_called_once_with(1)
        mock_event_repo.find_by_id.assert_called_once_with(1)
        mock_message_repo.save.assert_called_once()
        mock_event_bus.publish.assert_called()  # 验证领域事件被发布

    @patch('app.application.use_cases.events.add_event_message_use_case.RepositoryFactory')
    def test_should_fail_when_event_not_found(self, mock_repo_factory):
        """应该在事件不存在时失败"""
        # Arrange
        mock_user_repo = Mock()
        mock_event_repo = Mock()

        mock_repo_factory.get_user_repository.return_value = mock_user_repo
        mock_repo_factory.get_community_event_repository.return_value = mock_event_repo

        user = Mock()
        user.user_id = 1
        mock_user_repo.find_by_id.return_value = user

        mock_event_repo.find_by_id.return_value = None

        use_case = AddEventMessageUseCase()

        # Act
        result = use_case.execute(
            event_id=999,
            user_id=1,
            message='这是一条消息'
        )

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.NOT_FOUND
        assert '事件不存在' in result.message

    @patch('app.application.use_cases.events.add_event_message_use_case.RepositoryFactory')
    def test_should_fail_when_user_not_found(self, mock_repo_factory):
        """应该在用户不存在时失败"""
        # Arrange
        mock_user_repo = Mock()
        mock_event_repo = Mock()

        mock_repo_factory.get_user_repository.return_value = mock_user_repo
        mock_repo_factory.get_community_event_repository.return_value = mock_event_repo

        mock_user_repo.find_by_id.return_value = None

        use_case = AddEventMessageUseCase()

        # Act
        result = use_case.execute(
            event_id=1,
            user_id=999,
            message='这是一条消息'
        )

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.NOT_FOUND
        assert '用户不存在' in result.message

    @patch('app.application.use_cases.events.add_event_message_use_case.RepositoryFactory')
    def test_should_fail_when_event_already_closed(self, mock_repo_factory):
        """应该在事件已关闭时失败"""
        # Arrange
        mock_user_repo = Mock()
        mock_event_repo = Mock()

        mock_repo_factory.get_user_repository.return_value = mock_user_repo
        mock_repo_factory.get_community_event_repository.return_value = mock_event_repo

        user = Mock()
        user.user_id = 1
        mock_user_repo.find_by_id.return_value = user

        event = Mock()
        event.event_id = 1
        event.status = 2  # 已关闭
        mock_event_repo.find_by_id.return_value = event

        use_case = AddEventMessageUseCase()

        # Act
        result = use_case.execute(
            event_id=1,
            user_id=1,
            message='这是一条消息'
        )

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.BUSINESS_ERROR
        assert '事件已关闭' in result.message

    @patch('app.application.use_cases.events.add_event_message_use_case.RepositoryFactory')
    def test_should_fail_when_event_id_is_empty(self, mock_repo_factory):
        """应该在事件ID为空时失败"""
        # Arrange
        use_case = AddEventMessageUseCase()

        # Act
        result = use_case.execute(
            event_id=None,
            user_id=1,
            message='这是一条消息'
        )

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '参数不能为空' in result.message

    @patch('app.application.use_cases.events.add_event_message_use_case.RepositoryFactory')
    def test_should_fail_when_user_id_is_empty(self, mock_repo_factory):
        """应该在用户ID为空时失败"""
        # Arrange
        use_case = AddEventMessageUseCase()

        # Act
        result = use_case.execute(
            event_id=1,
            user_id=None,
            message='这是一条消息'
        )

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '参数不能为空' in result.message

    @patch('app.application.use_cases.events.add_event_message_use_case.RepositoryFactory')
    def test_should_fail_when_message_is_empty(self, mock_repo_factory):
        """应该在消息为空时失败"""
        # Arrange
        use_case = AddEventMessageUseCase()

        # Act
        result = use_case.execute(
            event_id=1,
            user_id=1,
            message=None
        )

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '参数不能为空' in result.message

    @patch('app.application.use_cases.events.add_event_message_use_case.RepositoryFactory')
    @patch('app.application.use_cases.events.add_event_message_use_case.EventBus')
    def test_should_add_message_with_different_type(self, mock_event_bus, mock_repo_factory):
        """应该成功添加不同类型的消息"""
        # Arrange
        mock_user_repo = Mock()
        mock_event_repo = Mock()
        mock_message_repo = Mock()

        mock_repo_factory.get_user_repository.return_value = mock_user_repo
        mock_repo_factory.get_community_event_repository.return_value = mock_event_repo
        mock_repo_factory.get_event_message_repository.return_value = mock_message_repo

        user = Mock()
        user.user_id = 1
        mock_user_repo.find_by_id.return_value = user

        event = Mock()
        event.event_id = 1
        event.status = 1
        mock_event_repo.find_by_id.return_value = event

        saved_message = Mock()
        saved_message.message_id = 1
        mock_message_repo.save.return_value = saved_message

        mock_event_bus_instance = Mock()
        mock_event_bus.return_value = mock_event_bus_instance

        use_case = AddEventMessageUseCase()

        # Act
        result = use_case.execute(
            event_id=1,
            user_id=1,
            message='图片消息',
            message_type='image'
        )

        # Assert
        assert result.is_success
        assert result.status == UseCaseStatus.SUCCESS
        mock_message_repo.save.assert_called_once()

    @patch('app.application.use_cases.events.add_event_message_use_case.RepositoryFactory')
    @patch('app.application.use_cases.events.add_event_message_use_case.EventBus')
    def test_should_handle_repository_exception(self, mock_event_bus, mock_repo_factory):
        """应该处理Repository异常"""
        # Arrange
        mock_user_repo = Mock()
        mock_event_repo = Mock()

        mock_repo_factory.get_user_repository.return_value = mock_user_repo
        mock_repo_factory.get_community_event_repository.return_value = mock_event_repo

        user = Mock()
        user.user_id = 1
        mock_user_repo.find_by_id.return_value = user

        mock_event_repo.find_by_id.side_effect = Exception('Database error')

        mock_event_bus_instance = Mock()
        mock_event_bus.return_value = mock_event_bus_instance

        use_case = AddEventMessageUseCase()

        # Act
        result = use_case.execute(
            event_id=1,
            user_id=1,
            message='这是一条消息'
        )

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.FAILURE
        assert '添加消息失败' in result.message