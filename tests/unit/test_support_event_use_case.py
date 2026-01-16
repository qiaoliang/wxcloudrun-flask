"""
SupportEventUseCase单元测试
"""
import pytest
from unittest.mock import Mock, patch
from app.application.use_cases.events.support_event_use_case import SupportEventUseCase
from app.application.use_cases.base import UseCaseStatus


class TestSupportEventUseCase:
    """测试SupportEventUseCase"""

    @patch('app.application.use_cases.events.support_event_use_case.RepositoryFactory')
    @patch('app.application.use_cases.events.support_event_use_case.EventBus')
    def test_should_successfully_support_event(self, mock_event_bus, mock_repo_factory):
        """应该成功支持事件"""
        # Arrange - 准备测试数据和Mock
        mock_user_repo = Mock()
        mock_event_repo = Mock()
        mock_message_repo = Mock()
        mock_staff_repo = Mock()

        mock_repo_factory.get_user_repository.return_value = mock_user_repo
        mock_repo_factory.get_community_event_repository.return_value = mock_event_repo
        mock_repo_factory.get_event_message_repository.return_value = mock_message_repo
        mock_repo_factory.get_community_staff_repository.return_value = mock_staff_repo

        # Mock用户
        sender = Mock()
        sender.user_id = 1
        mock_user_repo.find_by_id.return_value = sender

        # Mock事件
        event = Mock()
        event.event_id = 1
        event.community_id = 100
        event.status = 1  # 进行中
        mock_event_repo.find_by_id.return_value = event

        # Mock工作人员权限
        mock_staff_repo.exists.return_value = True

        # Mock已存在消息（空列表，表示没有应援过）
        mock_message_repo.find_active_by_event_id.return_value = []

        # Mock保存的消息
        saved_message = Mock()
        saved_message.message_id = 1
        saved_message.event_id = 1
        saved_message.sender_id = 1
        saved_message.message_content = '我来帮忙'
        saved_message.status = 1
        saved_message.created_at = Mock()
        saved_message.created_at.isoformat.return_value = '2026-01-16T10:00:00'
        mock_message_repo.save.return_value = saved_message

        mock_event_bus_instance = Mock()
        mock_event_bus.return_value = mock_event_bus_instance

        use_case = SupportEventUseCase()

        # Act - 执行被测试的方法
        result = use_case.execute(
            sender_id=1,
            event_id=1,
            message_content='我来帮忙'
        )

        # Assert - 验证行为
        assert result.is_success
        assert result.status == UseCaseStatus.SUCCESS
        assert '应援成功' in result.message
        assert result.data['support']['message_id'] == 1
        mock_user_repo.find_by_id.assert_called_once_with(1)
        mock_event_repo.find_by_id.assert_called_once_with(1)
        mock_staff_repo.exists.assert_called_once_with(100, 1)
        mock_message_repo.save.assert_called_once()
        mock_event_bus_instance.publish.assert_called()  # 验证领域事件被发布

    @patch('app.application.use_cases.events.support_event_use_case.RepositoryFactory')
    def test_should_fail_when_event_not_found(self, mock_repo_factory):
        """应该在事件不存在时失败"""
        # Arrange
        mock_user_repo = Mock()
        mock_event_repo = Mock()

        mock_repo_factory.get_user_repository.return_value = mock_user_repo
        mock_repo_factory.get_community_event_repository.return_value = mock_event_repo

        sender = Mock()
        sender.user_id = 1
        mock_user_repo.find_by_id.return_value = sender

        mock_event_repo.find_by_id.return_value = None

        use_case = SupportEventUseCase()

        # Act
        result = use_case.execute(
            sender_id=1,
            event_id=999,
            message_content='我来帮忙'
        )

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.NOT_FOUND
        assert '事件不存在' in result.message

    @patch('app.application.use_cases.events.support_event_use_case.RepositoryFactory')
    def test_should_fail_when_sender_not_found(self, mock_repo_factory):
        """应该在发送者不存在时失败"""
        # Arrange
        mock_user_repo = Mock()
        mock_event_repo = Mock()

        mock_repo_factory.get_user_repository.return_value = mock_user_repo
        mock_repo_factory.get_community_event_repository.return_value = mock_event_repo

        mock_user_repo.find_by_id.return_value = None

        use_case = SupportEventUseCase()

        # Act
        result = use_case.execute(
            sender_id=999,
            event_id=1,
            message_content='我来帮忙'
        )

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.NOT_FOUND
        assert '发送者不存在' in result.message

    @patch('app.application.use_cases.events.support_event_use_case.RepositoryFactory')
    def test_should_fail_when_event_already_closed(self, mock_repo_factory):
        """应该在事件已关闭时失败"""
        # Arrange
        mock_user_repo = Mock()
        mock_event_repo = Mock()
        mock_staff_repo = Mock()

        mock_repo_factory.get_user_repository.return_value = mock_user_repo
        mock_repo_factory.get_community_event_repository.return_value = mock_event_repo
        mock_repo_factory.get_community_staff_repository.return_value = mock_staff_repo

        sender = Mock()
        sender.user_id = 1
        mock_user_repo.find_by_id.return_value = sender

        event = Mock()
        event.event_id = 1
        event.community_id = 100
        event.status = 2  # 已关闭
        mock_event_repo.find_by_id.return_value = event

        mock_staff_repo.exists.return_value = True

        use_case = SupportEventUseCase()

        # Act
        result = use_case.execute(
            sender_id=1,
            event_id=1,
            message_content='我来帮忙'
        )

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.BUSINESS_ERROR
        assert '事件已关闭' in result.message

    @patch('app.application.use_cases.events.support_event_use_case.RepositoryFactory')
    def test_should_fail_when_no_permission(self, mock_repo_factory):
        """应该在无权限时失败"""
        # Arrange
        mock_user_repo = Mock()
        mock_event_repo = Mock()
        mock_staff_repo = Mock()

        mock_repo_factory.get_user_repository.return_value = mock_user_repo
        mock_repo_factory.get_community_event_repository.return_value = mock_event_repo
        mock_repo_factory.get_community_staff_repository.return_value = mock_staff_repo

        sender = Mock()
        sender.user_id = 1
        mock_user_repo.find_by_id.return_value = sender

        event = Mock()
        event.event_id = 1
        event.community_id = 100
        event.status = 1
        mock_event_repo.find_by_id.return_value = event

        mock_staff_repo.exists.return_value = False  # 无权限

        use_case = SupportEventUseCase()

        # Act
        result = use_case.execute(
            sender_id=1,
            event_id=1,
            message_content='我来帮忙'
        )

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.FORBIDDEN
        assert '无权限进行应援操作' in result.message

    @patch('app.application.use_cases.events.support_event_use_case.RepositoryFactory')
    def test_should_fail_when_already_supported(self, mock_repo_factory):
        """应该在已经应援过时失败"""
        # Arrange
        mock_user_repo = Mock()
        mock_event_repo = Mock()
        mock_message_repo = Mock()
        mock_staff_repo = Mock()

        mock_repo_factory.get_user_repository.return_value = mock_user_repo
        mock_repo_factory.get_community_event_repository.return_value = mock_event_repo
        mock_repo_factory.get_event_message_repository.return_value = mock_message_repo
        mock_repo_factory.get_community_staff_repository.return_value = mock_staff_repo

        sender = Mock()
        sender.user_id = 1
        mock_user_repo.find_by_id.return_value = sender

        event = Mock()
        event.event_id = 1
        event.community_id = 100
        event.status = 1
        mock_event_repo.find_by_id.return_value = event

        mock_staff_repo.exists.return_value = True

        # Mock已存在消息（包含用户的消息）
        existing_message = Mock()
        existing_message.sender_id = 1
        mock_message_repo.find_active_by_event_id.return_value = [existing_message]

        use_case = SupportEventUseCase()

        # Act
        result = use_case.execute(
            sender_id=1,
            event_id=1,
            message_content='我来帮忙'
        )

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.BUSINESS_ERROR
        assert '您已经应援过该事件' in result.message

    @patch('app.application.use_cases.events.support_event_use_case.RepositoryFactory')
    @patch('app.application.use_cases.events.support_event_use_case.EventBus')
    def test_should_handle_repository_exception(self, mock_event_bus, mock_repo_factory):
        """应该处理Repository异常"""
        # Arrange
        mock_user_repo = Mock()
        mock_event_repo = Mock()

        mock_repo_factory.get_user_repository.return_value = mock_user_repo
        mock_repo_factory.get_community_event_repository.return_value = mock_event_repo

        sender = Mock()
        sender.user_id = 1
        mock_user_repo.find_by_id.return_value = sender

        mock_event_repo.find_by_id.side_effect = Exception('Database error')

        mock_event_bus_instance = Mock()
        mock_event_bus.return_value = mock_event_bus_instance

        use_case = SupportEventUseCase()

        # Act
        result = use_case.execute(
            sender_id=1,
            event_id=1,
            message_content='我来帮忙'
        )

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.FAILURE
        assert '应援失败' in result.message