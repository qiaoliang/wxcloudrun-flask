"""
事件管理模块 UseCases 单元测试

测试以下 UseCase：
1. CreateEventUseCase - 创建社区事件
2. CloseEventUseCase - 关闭事件
3. SupportEventUseCase - 支持事件
4. GetCommunityEventsUseCase - 获取社区事件列表
5. GetEventDetailsUseCase - 获取事件详情
6. UpdateEventLocationUseCase - 更新事件位置
7. AddEventMessageUseCase - 添加事件消息
8. GetPendingEventsUseCase - 获取未处理事件
9. GetCommunityStatsUseCase - 获取社区统计

测试原则：
- 使用 AAA 模式（Arrange-Act-Assert）
- 测试行为而非实现细节
- 一个测试只验证一件事
- 清晰的测试命名
- 使用 mock 来隔离依赖
"""
import pytest
import datetime
from unittest.mock import Mock, patch, MagicMock
from database.flask_models import User, Community, CommunityEvent, EventMessage
from app.application.use_cases.events.create_event_use_case import CreateEventUseCase
from app.application.use_cases.events.close_event_use_case import CloseEventUseCase
from app.application.use_cases.events.support_event_use_case import SupportEventUseCase
from app.application.use_cases.events.get_community_events_use_case import GetCommunityEventsUseCase
from app.application.use_cases.events.get_event_details_use_case import GetEventDetailsUseCase
from app.application.use_cases.events.update_event_location_use_case import UpdateEventLocationUseCase
from app.application.use_cases.events.add_event_message_use_case import AddEventMessageUseCase
from app.application.use_cases.events.get_pending_events_use_case import GetPendingEventsUseCase
from app.application.use_cases.events.get_community_stats_use_case import GetCommunityStatsUseCase
from app.application.use_cases.base import UseCaseStatus


class TestCreateEventUseCase:
    """CreateEventUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return CreateEventUseCase()

    @pytest.fixture
    def mock_event_data(self):
        """测试事件数据"""
        return {
            'user_id': 1,
            'community_id': 1,
            'title': '测试求助事件',
            'description': '这是一个测试描述',
            'event_type': 'call_for_help',
            'location': '测试地点',
            'target_user_id': 2
        }

    def test_execute_success_call_for_help(self, use_case, test_user, test_community, mock_event_data):
        """
        测试执行成功 - 创建一键求助事件
        Given: 有效的用户、社区和事件数据
        When: 调用 execute 方法创建 call_for_help 类型事件
        Then: 返回 SUCCESS 状态，事件创建成功
        """
        # Arrange
        test_user.community_id = test_community.community_id
        mock_event_data['user_id'] = test_user.user_id
        mock_event_data['community_id'] = test_community.community_id

        # Act
        result = use_case.execute(**mock_event_data)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "事件创建成功" in result.message
        assert result.data['event']['event_id'] > 0
        assert result.data['event']['event_type'] == 'call_for_help'
        assert result.data['event']['status'] == 1
        assert result.data['event']['target_user_id'] == mock_event_data['target_user_id']

    def test_execute_success_supporting_event(self, use_case, test_user, test_community, mock_event_data):
        """
        测试执行成功 - 创建支持事件
        Given: 有效的用户、社区和事件数据
        When: 调用 execute 方法创建 supporting 类型事件
        Then: 返回 SUCCESS 状态，事件创建成功
        """
        # Arrange
        test_user.community_id = test_community.community_id
        mock_event_data['user_id'] = test_user.user_id
        mock_event_data['community_id'] = test_community.community_id
        mock_event_data['event_type'] = 'supporting'
        mock_event_data['target_user_id'] = None

        # Act
        result = use_case.execute(**mock_event_data)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "事件创建成功" in result.message
        assert result.data['event']['event_id'] > 0
        assert result.data['event']['event_type'] == 'supporting'
        assert result.data['event']['target_user_id'] is None

    def test_execute_validation_error_empty_title(self, use_case, test_user, test_community, mock_event_data):
        """
        测试验证失败 - 事件标题为空
        Given: 事件标题为空
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        test_user.community_id = test_community.community_id
        mock_event_data['user_id'] = test_user.user_id
        mock_event_data['community_id'] = test_community.community_id
        mock_event_data['title'] = ""

        # Act
        result = use_case.execute(**mock_event_data)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "事件标题不能为空" in result.message

    def test_execute_validation_error_invalid_event_type(self, use_case, test_user, test_community, mock_event_data):
        """
        测试验证失败 - 无效的事件类型
        Given: 事件类型不是 call_for_help 或 supporting
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        test_user.community_id = test_community.community_id
        mock_event_data['user_id'] = test_user.user_id
        mock_event_data['community_id'] = test_community.community_id
        mock_event_data['event_type'] = 'invalid_type'

        # Act
        result = use_case.execute(**mock_event_data)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "无效的事件类型" in result.message

    def test_execute_not_found_user_not_exists(self, use_case, test_community, mock_event_data):
        """
        测试执行失败 - 用户不存在
        Given: 用户ID不存在
        When: 调用 execute 方法
        Then: 返回 NOT_FOUND 状态
        """
        # Arrange
        mock_event_data['community_id'] = test_community.community_id
        mock_event_data['user_id'] = 99999

        # Act
        result = use_case.execute(**mock_event_data)

        # Assert
        assert result.status == UseCaseStatus.NOT_FOUND
        assert "用户不存在" in result.message

    def test_execute_not_found_community_not_exists(self, use_case, test_user, mock_event_data):
        """
        测试执行失败 - 社区不存在
        Given: 社区ID不存在
        When: 调用 execute 方法
        Then: 返回 NOT_FOUND 状态
        """
        # Arrange
        mock_event_data['user_id'] = test_user.user_id
        mock_event_data['community_id'] = 99999

        # Act
        result = use_case.execute(**mock_event_data)

        # Assert
        assert result.status == UseCaseStatus.NOT_FOUND
        assert "社区不存在" in result.message

    def test_execute_forbidden_user_not_in_community(self, use_case, test_user, test_community, mock_event_data):
        """
        测试执行失败 - 用户不属于该社区
        Given: 用户不属于该社区
        When: 调用 execute 方法
        Then: 返回 FORBIDDEN 状态
        """
        # Arrange
        test_user.community_id = 99999  # 用户不属于测试社区
        mock_event_data['user_id'] = test_user.user_id
        mock_event_data['community_id'] = test_community.community_id

        # Act
        result = use_case.execute(**mock_event_data)

        # Assert
        assert result.status == UseCaseStatus.FORBIDDEN
        assert "用户不属于该社区" in result.message

    def test_execute_business_error_duplicate_call_for_help(self, use_case, test_user, test_community, mock_event_data):
        """
        测试执行失败 - 用户已有进行中的一键求助事件
        Given: 目标用户已有进行中的一键求助事件
        When: 调用 execute 方法创建新的一键求助事件
        Then: 返回 BUSINESS_ERROR 状态
        """
        # Arrange
        test_user.community_id = test_community.community_id
        target_user = test_user

        # 创建第一个进行中的一键求助事件
        existing_event = CommunityEvent(
            community_id=test_community.community_id,
            title='第一个求助事件',
            description='第一个测试描述',
            event_type='call_for_help',
            target_user_id=target_user.user_id,
            created_by=test_user.user_id,
            status=1,
            created_at=datetime.datetime.now()
        )
        use_case.community_event_repository.save(existing_event)

        # 尝试创建第二个一键求助事件
        mock_event_data['user_id'] = test_user.user_id
        mock_event_data['community_id'] = test_community.community_id
        mock_event_data['target_user_id'] = target_user.user_id

        # Act
        result = use_case.execute(**mock_event_data)

        # Assert
        assert result.status == UseCaseStatus.BUSINESS_ERROR
        assert "您已有进行中的求助事件" in result.message

    def test_execute_success_minimal_params(self, use_case, test_user, test_community, mock_event_data):
        """
        测试执行成功 - 最少参数
        Given: 只提供必填参数
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，事件创建成功
        """
        # Arrange
        test_user.community_id = test_community.community_id
        minimal_data = {
            'user_id': test_user.user_id,
            'community_id': test_community.community_id,
            'title': '最小参数测试'
        }

        # Act
        result = use_case.execute(**minimal_data)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['event']['event_id'] > 0
        assert result.data['event']['event_type'] == 'call_for_help'  # 默认值
        # 注意：返回数据中不包含 description 和 location 字段


class TestCloseEventUseCase:
    """CloseEventUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return CloseEventUseCase()

    @pytest.fixture
    def test_event(self, test_user, test_community, test_session):
        """创建测试事件"""
        event = CommunityEvent(
            community_id=test_community.community_id,
            title='测试事件',
            description='测试描述',
            event_type='call_for_help',
            target_user_id=test_user.user_id,
            created_by=test_user.user_id,
            status=1,
            created_at=datetime.datetime.now()
        )
        test_session.add(event)
        test_session.flush()
        return event

    def test_execute_success_by_creator(self, use_case, test_user, test_event):
        """
        测试执行成功 - 事件发起者关闭事件
        Given: 事件发起者关闭自己创建的事件
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，事件关闭成功
        """
        # Arrange
        closure_reason = '测试关闭原因，长度超过10个字符'

        # Act
        result = use_case.execute(
            user_id=test_user.user_id,
            event_id=test_event.event_id,
            closure_reason=closure_reason
        )

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "事件已关闭" in result.message
        assert result.data['closed_by'] == test_user.user_id
        assert result.data['closure_type'] == 1  # 用户关闭
        assert result.data['closure_reason'] == closure_reason
        assert result.data['closed_at'] is not None

    def test_execute_success_by_staff(self, use_case, test_event, test_staff_user):
        """
        测试执行成功 - 工作人员关闭事件
        Given: 社区工作人员关闭事件
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，事件关闭成功
        """
        # Arrange
        closure_reason = '工作人员关闭事件，测试关闭原因的长度要求'

        # Act
        result = use_case.execute(
            user_id=test_staff_user.user_id,
            event_id=test_event.event_id,
            closure_reason=closure_reason
        )

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['closed_by'] == test_staff_user.user_id
        assert result.data['closure_type'] == 2  # 工作人员关闭
        assert result.data['closure_reason'] == closure_reason

    def test_execute_success_by_target_user(self, use_case, test_event, test_user):
        """
        测试执行成功 - 目标用户关闭事件
        Given: 目标用户关闭事件
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，事件关闭成功
        """
        # Arrange
        test_event.target_user_id = test_user.user_id
        test_event.created_by = 99999  # 创建者是其他人
        closure_reason = '目标用户关闭事件，测试关闭原因'

        # Act
        result = use_case.execute(
            user_id=test_user.user_id,
            event_id=test_event.event_id,
            closure_reason=closure_reason
        )

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['closed_by'] == test_user.user_id
        assert result.data['closure_type'] == 1  # 用户关闭

    def test_execute_validation_error_missing_event_id(self, use_case):
        """
        测试验证失败 - 缺少事件ID
        Given: 事件ID为空
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        result = use_case.execute(
            user_id=1,
            event_id=None,
            closure_reason='测试关闭原因'
        )

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "事件ID不能为空" in result.message

    def test_execute_validation_error_closure_reason_too_short(self, use_case, test_event):
        """
        测试验证失败 - 关闭原因太短
        Given: 关闭原因少于10个字符
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        closure_reason = '太短'

        # Act
        result = use_case.execute(
            user_id=1,
            event_id=test_event.event_id,
            closure_reason=closure_reason
        )

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "关闭原因长度必须在10-500字符之间" in result.message

    def test_execute_validation_error_closure_reason_too_long(self, use_case, test_event):
        """
        测试验证失败 - 关闭原因太长
        Given: 关闭原因超过500个字符
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        closure_reason = 'a' * 501

        # Act
        result = use_case.execute(
            user_id=1,
            event_id=test_event.event_id,
            closure_reason=closure_reason
        )

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "关闭原因长度必须在10-500字符之间" in result.message

    def test_execute_not_found_event_not_exists(self, use_case, test_user):
        """
        测试执行失败 - 事件不存在
        Given: 事件ID不存在
        When: 调用 execute 方法
        Then: 返回 NOT_FOUND 状态
        """
        # Arrange
        closure_reason = '测试关闭原因，长度足够'

        # Act
        result = use_case.execute(
            user_id=test_user.user_id,
            event_id=99999,
            closure_reason=closure_reason
        )

        # Assert
        assert result.status == UseCaseStatus.NOT_FOUND
        assert "事件不存在" in result.message

    def test_execute_business_error_event_already_closed(self, use_case, test_event):
        """
        测试执行失败 - 事件已关闭
        Given: 事件状态不是进行中
        When: 调用 execute 方法
        Then: 返回 BUSINESS_ERROR 状态
        """
        # Arrange
        test_event.status = 2  # 已解决
        use_case.community_event_repository.save(test_event)
        closure_reason = '测试关闭原因，长度超过10个字符'

        # Act
        result = use_case.execute(
            user_id=1,
            event_id=test_event.event_id,
            closure_reason=closure_reason
        )

        # Assert
        assert result.status == UseCaseStatus.BUSINESS_ERROR
        assert "无法关闭" in result.message

    def test_execute_forbidden_no_permission(self, use_case, test_event, test_user):
        """
        测试执行失败 - 无权限关闭事件
        Given: 用户不是事件发起者、目标用户或社区工作人员
        When: 调用 execute 方法
        Then: 返回 FORBIDDEN 状态
        """
        # Arrange
        test_event.created_by = 99999
        test_event.target_user_id = 99998
        use_case.community_event_repository.save(test_event)
        closure_reason = '测试关闭原因，长度超过10个字符'

        # Act
        result = use_case.execute(
            user_id=test_user.user_id,
            event_id=test_event.event_id,
            closure_reason=closure_reason
        )

        # Assert
        assert result.status == UseCaseStatus.FORBIDDEN
        assert "只有事件发起者、目标用户或社区工作人员可以关闭事件" in result.message

    def test_execute_not_found_user_not_exists(self, use_case, test_event):
        """
        测试执行失败 - 用户不存在
        Given: 用户ID不存在
        When: 调用 execute 方法
        Then: 返回 NOT_FOUND 状态
        """
        # Arrange
        closure_reason = '测试关闭原因，长度超过10个字符'

        # Act
        result = use_case.execute(
            user_id=99999,
            event_id=test_event.event_id,
            closure_reason=closure_reason
        )

        # Assert
        assert result.status == UseCaseStatus.NOT_FOUND
        assert "用户不存在" in result.message


class TestSupportEventUseCase:
    """SupportEventUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return SupportEventUseCase()

    @pytest.fixture
    def test_event(self, test_user, test_community, test_session):
        """创建测试事件"""
        event = CommunityEvent(
            community_id=test_community.community_id,
            title='测试事件',
            description='测试描述',
            event_type='call_for_help',
            target_user_id=test_user.user_id,
            created_by=test_user.user_id,
            status=1,
            created_at=datetime.datetime.now()
        )
        test_session.add(event)
        test_session.flush()
        return event

    def test_execute_success(self, use_case, test_event, test_staff_user):
        """
        测试执行成功 - 工作人员应援事件
        Given: 社区工作人员对进行中的事件进行应援
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，应援创建成功
        """
        # Arrange
        message_content = '我来帮助您'

        # Act
        result = use_case.execute(
            sender_id=test_staff_user.user_id,
            event_id=test_event.event_id,
            message_content=message_content
        )

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "应援成功" in result.message
        assert result.data['support']['message_id'] > 0
        assert result.data['support']['event_id'] == test_event.event_id
        assert result.data['support']['sender_id'] == test_staff_user.user_id
        assert result.data['support']['message_content'] == message_content
        assert result.data['support']['status'] == 1

    def test_execute_validation_error_missing_event_id(self, use_case, test_staff_user):
        """
        测试验证失败 - 缺少事件ID
        Given: 事件ID为空
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        result = use_case.execute(
            sender_id=test_staff_user.user_id,
            event_id=None,
            message_content='测试消息'
        )

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "事件ID不能为空" in result.message

    def test_execute_not_found_sender_not_exists(self, use_case, test_event):
        """
        测试执行失败 - 发送者不存在
        Given: 发送者ID不存在
        When: 调用 execute 方法
        Then: 返回 NOT_FOUND 状态
        """
        # Arrange
        result = use_case.execute(
            sender_id=99999,
            event_id=test_event.event_id,
            message_content='测试消息'
        )

        # Assert
        assert result.status == UseCaseStatus.NOT_FOUND
        assert "发送者不存在" in result.message

    def test_execute_not_found_event_not_exists(self, use_case, test_staff_user):
        """
        测试执行失败 - 事件不存在
        Given: 事件ID不存在
        When: 调用 execute 方法
        Then: 返回 NOT_FOUND 状态
        """
        # Arrange
        result = use_case.execute(
            sender_id=test_staff_user.user_id,
            event_id=99999,
            message_content='测试消息'
        )

        # Assert
        assert result.status == UseCaseStatus.NOT_FOUND
        assert "事件不存在" in result.message

    def test_execute_business_error_event_closed(self, use_case, test_event, test_staff_user):
        """
        测试执行失败 - 事件已关闭
        Given: 事件状态不是进行中
        When: 调用 execute 方法
        Then: 返回 BUSINESS_ERROR 状态
        """
        # Arrange
        test_event.status = 2  # 已解决
        use_case.community_event_repository.save(test_event)

        # Act
        result = use_case.execute(
            sender_id=test_staff_user.user_id,
            event_id=test_event.event_id,
            message_content='测试消息'
        )

        # Assert
        assert result.status == UseCaseStatus.BUSINESS_ERROR
        assert "事件已关闭，无法添加消息" in result.message

    def test_execute_forbidden_not_staff(self, use_case, test_event, test_user):
        """
        测试执行失败 - 发送者不是社区工作人员
        Given: 发送者不是社区工作人员
        When: 调用 execute 方法
        Then: 返回 FORBIDDEN 状态
        """
        # Arrange
        test_user.role = 1  # 普通用户

        # Act
        result = use_case.execute(
            sender_id=test_user.user_id,
            event_id=test_event.event_id,
            message_content='测试消息'
        )

        # Assert
        assert result.status == UseCaseStatus.FORBIDDEN
        assert "无权限进行应援操作" in result.message

    def test_execute_business_error_already_supported(self, use_case, test_event, test_staff_user):
        """
        测试执行失败 - 已经应援过
        Given: 发送者已经应援过该事件
        When: 调用 execute 方法再次应援
        Then: 返回 BUSINESS_ERROR 状态
        """
        # Arrange
        # 创建第一个应援
        first_support = EventMessage(
            event_id=test_event.event_id,
            sender_id=test_staff_user.user_id,
            message_content='第一次应援',
            message_type='text',
            status=1,
            created_at=datetime.datetime.now()
        )
        use_case.event_message_repository.save(first_support)

        # Act
        result = use_case.execute(
            sender_id=test_staff_user.user_id,
            event_id=test_event.event_id,
            message_content='第二次应援'
        )

        # Assert
        assert result.status == UseCaseStatus.BUSINESS_ERROR
        assert "您已经应援过该事件" in result.message

    def test_execute_success_empty_message(self, use_case, test_event, test_staff_user):
        """
        测试执行成功 - 空消息内容
        Given: 消息内容为空
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，应援创建成功
        """
        # Arrange
        message_content = ""

        # Act
        result = use_case.execute(
            sender_id=test_staff_user.user_id,
            event_id=test_event.event_id,
            message_content=message_content
        )

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['support']['message_content'] == message_content


class TestGetCommunityEventsUseCase:
    """GetCommunityEventsUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return GetCommunityEventsUseCase()

    @pytest.fixture
    def test_events(self, test_user, test_community, test_session):
        """创建多个测试事件"""
        events = []
        for i in range(5):
            event = CommunityEvent(
                community_id=test_community.community_id,
                title=f'测试事件{i}',
                description=f'测试描述{i}',
                event_type='call_for_help' if i % 2 == 0 else 'supporting',
                target_user_id=test_user.user_id if i % 2 == 0 else None,
                created_by=test_user.user_id,
                status=1 if i < 3 else 2,
                created_at=datetime.datetime.now() - datetime.timedelta(hours=i)
            )
            events.append(test_session.add(event))
        return events

    def test_execute_success_all_events(self, use_case, test_community, test_events):
        """
        测试执行成功 - 获取所有事件
        Given: 社区有多个事件
        When: 调用 execute 方法获取所有事件
        Then: 返回 SUCCESS 状态，返回所有事件
        """
        # Act
        result = use_case.execute(community_id=test_community.community_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "获取社区事件列表成功" in result.message
        assert result.data['total'] == len(test_events)
        assert len(result.data['events']) == len(test_events)
        assert result.data['page'] == 1
        assert result.data['page_size'] == 20

    def test_execute_success_filter_by_event_type(self, use_case, test_community, test_events):
        """
        测试执行成功 - 按事件类型筛选
        Given: 社区有多种类型的事件
        When: 调用 execute 方法并指定事件类型
        Then: 返回 SUCCESS 状态，只返回指定类型的事件
        """
        # Act
        result = use_case.execute(
            community_id=test_community.community_id,
            event_type='call_for_help'
        )

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        for event in result.data['events']:
            assert event['event_type'] == 'call_for_help'

    def test_execute_success_filter_by_status(self, use_case, test_community, test_events):
        """
        测试执行成功 - 按状态筛选
        Given: 社区有多种状态的事件
        When: 调用 execute 方法并指定状态
        Then: 返回 SUCCESS 状态，只返回指定状态的事件
        """
        # Act
        result = use_case.execute(
            community_id=test_community.community_id,
            status=1
        )

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        for event in result.data['events']:
            assert event['status'] == 1

    def test_execute_success_pagination(self, use_case, test_community, test_events):
        """
        测试执行成功 - 分页
        Given: 社区有多个事件
        When: 调用 execute 方法并指定分页参数
        Then: 返回 SUCCESS 状态，返回指定页的事件
        """
        # Act
        result = use_case.execute(
            community_id=test_community.community_id,
            page=1,
            page_size=2
        )

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert len(result.data['events']) == 2
        assert result.data['total_pages'] == 3  # (5 + 2 - 1) // 2 = 3

    def test_execute_validation_error_missing_community_id(self, use_case):
        """
        测试验证失败 - 缺少社区ID
        Given: 社区ID为空
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        result = use_case.execute(community_id=None)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "社区ID不能为空" in result.message

    def test_execute_validation_error_invalid_page(self, use_case, test_community):
        """
        测试验证失败 - 无效页码
        Given: 页码小于1
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        result = use_case.execute(community_id=test_community.community_id, page=0)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "页码必须大于0" in result.message

    def test_execute_validation_error_invalid_page_size(self, use_case, test_community):
        """
        测试验证失败 - 无效每页数量
        Given: 每页数量超出范围
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        result = use_case.execute(community_id=test_community.community_id, page_size=101)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "每页数量必须在1-100之间" in result.message

    def test_execute_not_found_community_not_exists(self, use_case):
        """
        测试执行失败 - 社区不存在
        Given: 社区ID不存在
        When: 调用 execute 方法
        Then: 返回 NOT_FOUND 状态
        """
        # Arrange
        result = use_case.execute(community_id=99999)

        # Assert
        assert result.status == UseCaseStatus.NOT_FOUND
        assert "社区不存在" in result.message

    def test_execute_success_empty_events(self, use_case, test_community):
        """
        测试执行成功 - 没有事件
        Given: 社区没有事件
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，返回空列表
        """
        # Act
        result = use_case.execute(community_id=test_community.community_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['total'] == 0
        assert len(result.data['events']) == 0


class TestGetEventDetailsUseCase:
    """GetEventDetailsUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return GetEventDetailsUseCase()

    @pytest.fixture
    def test_event(self, test_user, test_community, test_session):
        """创建测试事件"""
        event = CommunityEvent(
            community_id=test_community.community_id,
            title='测试事件',
            description='测试描述',
            event_type='call_for_help',
            target_user_id=test_user.user_id,
            created_by=test_user.user_id,
            status=1,
            created_at=datetime.datetime.now()
        )
        test_session.add(event)
        test_session.flush()
        return event

    def test_execute_success(self, use_case, test_event, test_user):
        """
        测试执行成功 - 获取事件详情
        Given: 事件存在
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，返回事件详情
        """
        # Act
        result = use_case.execute(event_id=test_event.event_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "获取事件详情成功" in result.message
        assert result.data['event']['event_id'] == test_event.event_id
        assert result.data['event']['title'] == test_event.title
        assert result.data['event']['target_user_id'] == test_user.user_id
        assert result.data['event']['target_user_name'] == test_user.nickname
        assert result.data['event']['target_user_avatar'] == test_user.avatar_url

    def test_execute_success_with_messages(self, use_case, test_event, test_user, test_session):
        """
        测试执行成功 - 事件有消息
        Given: 事件有多个消息
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，返回事件详情和消息列表
        """
        # Arrange
        message = EventMessage(
            event_id=test_event.event_id,
            sender_id=test_user.user_id,
            message_content='测试消息',
            message_type='text',
            status=1,
            created_at=datetime.datetime.now()
        )
        test_session.add(message)

        # Act
        result = use_case.execute(event_id=test_event.event_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert len(result.data['event']['messages']) == 1
        assert result.data['event']['message_count'] == 1
        assert result.data['event']['messages'][0]['sender_id'] == test_user.user_id
        assert result.data['event']['messages'][0]['sender_name'] == test_user.nickname

    def test_execute_validation_error_missing_event_id(self, use_case):
        """
        测试验证失败 - 缺少事件ID
        Given: 事件ID为空
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        result = use_case.execute(event_id=None)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "事件ID不能为空" in result.message

    def test_execute_not_found_event_not_exists(self, use_case):
        """
        测试执行失败 - 事件不存在
        Given: 事件ID不存在
        When: 调用 execute 方法
        Then: 返回 NOT_FOUND 状态
        """
        # Arrange
        result = use_case.execute(event_id=99999)

        # Assert
        assert result.status == UseCaseStatus.NOT_FOUND
        assert "事件不存在" in result.message

    def test_execute_success_without_target_user(self, use_case, test_community, test_session):
        """
        测试执行成功 - 事件没有目标用户
        Given: 事件没有目标用户
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，目标用户信息为 None
        """
        # Arrange
        event = CommunityEvent(
            community_id=test_community.community_id,
            title='测试事件',
            description='测试描述',
            event_type='supporting',
            target_user_id=None,
            created_by=1,
            status=1,
            created_at=datetime.datetime.now()
        )
        test_session.add(event)
        test_session.flush()

        # Act
        result = use_case.execute(event_id=event.event_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['event']['target_user_id'] is None
        assert result.data['event']['target_user_name'] is None
        assert result.data['event']['target_user_avatar'] is None

    def test_execute_success_filter_inactive_messages(self, use_case, test_event, test_user, test_session):
        """
        测试执行成功 - 过滤非活跃消息
        Given: 事件有多个消息，包括非活跃消息
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，只返回活跃消息
        """
        # Arrange
        active_message = EventMessage(
            event_id=test_event.event_id,
            sender_id=test_user.user_id,
            message_content='活跃消息',
            message_type='text',
            status=1,
            created_at=datetime.datetime.now()
        )
        inactive_message = EventMessage(
            event_id=test_event.event_id,
            sender_id=test_user.user_id,
            message_content='非活跃消息',
            message_type='text',
            status=2,  # 2=已取消
            created_at=datetime.datetime.now()
        )
        test_session.add(active_message)
        test_session.add(inactive_message)
        test_session.flush()

        # Act
        result = use_case.execute(event_id=test_event.event_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert len(result.data['event']['messages']) == 1
        assert result.data['event']['messages'][0]['message_content'] == '活跃消息'


class TestUpdateEventLocationUseCase:
    """UpdateEventLocationUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return UpdateEventLocationUseCase()

    @pytest.fixture
    def test_event(self, test_user, test_community, test_session):
        """创建测试事件"""
        event = CommunityEvent(
            community_id=test_community.community_id,
            title='测试事件',
            description='测试描述',
            event_type='call_for_help',
            target_user_id=test_user.user_id,
            created_by=test_user.user_id,
            status=1,
            created_at=datetime.datetime.now()
        )
        test_session.add(event)
        test_session.flush()
        return event

    def test_execute_success_by_target_user(self, use_case, test_event, test_user):
        """
        测试执行成功 - 目标用户更新位置
        Given: 目标用户更新事件位置
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，位置更新成功
        """
        # Arrange
        new_location = '新位置描述'
        new_lat = 39.9042
        new_lon = 116.4074

        # Act
        result = use_case.execute(
            event_id=test_event.event_id,
            user_id=test_user.user_id,
            location=new_location,
            location_lat=new_lat,
            location_lon=new_lon
        )

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "事件位置更新成功" in result.message
        assert result.data['location'] == new_location
        assert result.data['location_lat'] == new_lat
        assert result.data['location_lon'] == new_lon

    def test_execute_success_by_staff(self, use_case, test_event, test_staff_user):
        """
        测试执行成功 - 工作人员更新位置
        Given: 社区工作人员更新事件位置
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，位置更新成功
        """
        # Arrange
        new_location = '工作人员更新的位置'

        # Act
        result = use_case.execute(
            event_id=test_event.event_id,
            user_id=test_staff_user.user_id,
            location=new_location
        )

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['location'] == new_location

    def test_execute_validation_error_missing_event_id(self, use_case, test_user):
        """
        测试验证失败 - 缺少事件ID
        Given: 事件ID为空
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        result = use_case.execute(
            event_id=None,
            user_id=test_user.user_id,
            location='测试位置'
        )

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "事件ID不能为空" in result.message

    def test_execute_validation_error_missing_user_id(self, use_case):
        """
        测试验证失败 - 缺少用户ID
        Given: 用户ID为空
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        result = use_case.execute(
            event_id=1,
            user_id=None,
            location='测试位置'
        )

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "用户ID不能为空" in result.message

    def test_execute_validation_error_empty_location(self, use_case, test_user):
        """
        测试验证失败 - 位置描述为空
        Given: 位置描述为空
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        result = use_case.execute(
            event_id=1,
            user_id=test_user.user_id,
            location="  "
        )

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "位置描述不能为空" in result.message

    def test_execute_not_found_event_not_exists(self, use_case, test_user):
        """
        测试执行失败 - 事件不存在
        Given: 事件ID不存在
        When: 调用 execute 方法
        Then: 返回 NOT_FOUND 状态
        """
        # Arrange
        result = use_case.execute(
            event_id=99999,
            user_id=test_user.user_id,
            location='测试位置'
        )

        # Assert
        assert result.status == UseCaseStatus.NOT_FOUND
        assert "事件不存在" in result.message

    def test_execute_business_error_event_closed(self, use_case, test_event, test_user):
        """
        测试执行失败 - 事件已关闭
        Given: 事件状态不是进行中
        When: 调用 execute 方法
        Then: 返回 BUSINESS_ERROR 状态
        """
        # Arrange
        test_event.status = 2  # 已解决
        use_case.community_event_repository.save(test_event)

        # Act
        result = use_case.execute(
            event_id=test_event.event_id,
            user_id=test_user.user_id,
            location='测试位置'
        )

        # Assert
        assert result.status == UseCaseStatus.BUSINESS_ERROR
        assert "事件已关闭，无法更新位置" in result.message

    def test_execute_not_found_user_not_exists(self, use_case, test_event):
        """
        测试执行失败 - 用户不存在
        Given: 用户ID不存在
        When: 调用 execute 方法
        Then: 返回 NOT_FOUND 状态
        """
        # Arrange
        result = use_case.execute(
            event_id=test_event.event_id,
            user_id=99999,
            location='测试位置'
        )

        # Assert
        assert result.status == UseCaseStatus.NOT_FOUND
        assert "用户不存在" in result.message

    def test_execute_unauthorized_no_permission(self, use_case, test_event, test_user):
        """
        测试执行失败 - 无权限更新位置
        Given: 用户不是目标用户或社区工作人员
        When: 调用 execute 方法
        Then: 返回 UNAUTHORIZED 状态
        """
        # Arrange
        test_event.target_user_id = 99999
        use_case.community_event_repository.save(test_event)
        test_user.role = 1  # 普通用户

        # Act
        result = use_case.execute(
            event_id=test_event.event_id,
            user_id=test_user.user_id,
            location='测试位置'
        )

        # Assert
        assert result.status == UseCaseStatus.UNAUTHORIZED
        assert "无权更新此事件位置" in result.message


class TestAddEventMessageUseCase:
    """AddEventMessageUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return AddEventMessageUseCase()

    @pytest.fixture
    def test_event(self, test_user, test_community, test_session):
        """创建测试事件"""
        event = CommunityEvent(
            community_id=test_community.community_id,
            title='测试事件',
            description='测试描述',
            event_type='call_for_help',
            target_user_id=test_user.user_id,
            created_by=test_user.user_id,
            status=1,
            created_at=datetime.datetime.now()
        )
        test_session.add(event)
        test_session.commit()
        return event

    def test_execute_success_text_message(self, use_case, test_event, test_user):
        """
        测试执行成功 - 添加文本消息
        Given: 事件进行中，用户添加文本消息
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，消息添加成功
        """
        # Arrange
        message = '这是一条测试消息'

        # Act
        result = use_case.execute(
            event_id=test_event.event_id,
            user_id=test_user.user_id,
            message=message
        )

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "添加消息成功" in result.message
        assert result.data['message_id'] > 0

    def test_execute_success_image_message(self, use_case, test_event, test_user):
        """
        测试执行成功 - 添加图片消息
        Given: 用户添加图片消息
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，消息添加成功
        """
        # Arrange
        media_url = 'https://example.com/image.jpg'

        # Act
        result = use_case.execute(
            event_id=test_event.event_id,
            user_id=test_user.user_id,
            message='',
            media_url=media_url
        )

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['message_type'] == 'image'
        assert result.data['media_url'] == media_url

    def test_execute_success_voice_message(self, use_case, test_event, test_user):
        """
        测试执行成功 - 添加语音消息
        Given: 用户添加语音消息
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，消息添加成功
        """
        # Arrange
        media_url = 'https://example.com/voice.mp3'

        # Act
        result = use_case.execute(
            event_id=test_event.event_id,
            user_id=test_user.user_id,
            message='',
            media_url=media_url
        )

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['message_type'] == 'voice'
        assert result.data['media_url'] == media_url

    def test_execute_success_with_tags(self, use_case, test_event, test_user):
        """
        测试执行成功 - 添加带标签的消息
        Given: 用户添加带标签的消息
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，消息添加成功
        """
        # Arrange
        message_tags = ['已联系', '正在处理']

        # Act
        result = use_case.execute(
            event_id=test_event.event_id,
            user_id=test_user.user_id,
            message='',
            message_tags=message_tags
        )

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['message_tags'] == message_tags

    def test_execute_validation_error_missing_event_id(self, use_case, test_user):
        """
        测试验证失败 - 缺少事件ID
        Given: 事件ID为空
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        result = use_case.execute(
            event_id=None,
            user_id=test_user.user_id,
            message='测试消息'
        )

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "事件ID不能为空" in result.message

    def test_execute_validation_error_missing_sender_id(self, use_case):
        """
        测试验证失败 - 缺少发送者ID
        Given: 发送者ID为空
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        result = use_case.execute(
            event_id=1,
            sender_id=None,
            message='测试消息'
        )

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "发送者ID不能为空" in result.message

    def test_execute_validation_error_empty_content_no_media_no_tags(self, use_case, test_user):
        """
        测试验证失败 - 没有内容、媒体或标签
        Given: 没有文字内容、媒体文件或标签
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        result = use_case.execute(
            event_id=1,
            user_id=test_user.user_id,
            message='  ',
            media_url=None,
            message_tags=None
        )

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "请至少提供文字内容、媒体文件或快捷指令" in result.message

    def test_execute_not_found_event_not_exists(self, use_case, test_user):
        """
        测试执行失败 - 事件不存在
        Given: 事件ID不存在
        When: 调用 execute 方法
        Then: 返回 NOT_FOUND 状态
        """
        # Arrange
        result = use_case.execute(
            event_id=99999,
            user_id=test_user.user_id,
            message='测试消息'
        )

        # Assert
        assert result.status == UseCaseStatus.NOT_FOUND
        assert "事件不存在" in result.message

    def test_execute_business_error_event_closed(self, use_case, test_event, test_user):
        """
        测试执行失败 - 事件已关闭
        Given: 事件状态不是进行中
        When: 调用 execute 方法
        Then: 返回 BUSINESS_ERROR 状态
        """
        # Arrange
        test_event.status = 2  # 已解决
        use_case.community_event_repository.save(test_event)

        # Act
        result = use_case.execute(
            event_id=test_event.event_id,
            user_id=test_user.user_id,
            message='测试消息'
        )

        # Assert
        assert result.status == UseCaseStatus.BUSINESS_ERROR
        assert "事件已关闭，无法添加消息" in result.message

    def test_execute_not_found_sender_not_exists(self, use_case, test_event):
        """
        测试执行失败 - 发送者不存在
        Given: 发送者ID不存在
        When: 调用 execute 方法
        Then: 返回 NOT_FOUND 状态
        """
        # Arrange
        result = use_case.execute(
            event_id=test_event.event_id,
            sender_id=99999,
            message='测试消息'
        )

        # Assert
        assert result.status == UseCaseStatus.NOT_FOUND
        assert "发送者不存在" in result.message


class TestGetPendingEventsUseCase:
    """GetPendingEventsUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return GetPendingEventsUseCase()

    @pytest.fixture
    def test_events(self, test_user, test_community, test_session):
        """创建多个测试事件"""
        events = []
        for i in range(5):
            event = CommunityEvent(
                community_id=test_community.community_id,
                title=f'测试事件{i}',
                description=f'测试描述{i}',
                event_type='call_for_help',
                target_user_id=test_user.user_id,
                created_by=test_user.user_id,
                status=1 if i < 3 else 2,
                created_at=datetime.datetime.now() - datetime.timedelta(hours=i)
            )
            events.append(test_session.add(event))
        return events

    def test_execute_success(self, use_case, test_community, test_events):
        """
        测试执行成功 - 获取未处理事件
        Given: 社区有多个未处理的一键求助事件
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，返回未处理事件
        """
        # Act
        result = use_case.execute(community_id=test_community.community_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "获取未处理事件成功" in result.message
        assert result.data['count'] == 3  # 只有3个状态为1的事件
        assert len(result.data['events']) == 3

    def test_execute_validation_error_missing_community_id(self, use_case):
        """
        测试验证失败 - 缺少社区ID
        Given: 社区ID为空
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        result = use_case.execute(community_id=None)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "社区ID不能为空" in result.message

    def test_execute_not_found_community_not_exists(self, use_case):
        """
        测试执行失败 - 社区不存在
        Given: 社区ID不存在
        When: 调用 execute 方法
        Then: 返回 NOT_FOUND 状态
        """
        # Arrange
        result = use_case.execute(community_id=99999)

        # Assert
        assert result.status == UseCaseStatus.NOT_FOUND
        assert "社区不存在" in result.message

    def test_execute_success_no_pending_events(self, use_case, test_community):
        """
        测试执行成功 - 没有未处理事件
        Given: 社区没有未处理的一键求助事件
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，返回空列表
        """
        # Act
        result = use_case.execute(community_id=test_community.community_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['count'] == 0
        assert len(result.data['events']) == 0

    def test_execute_success_filter_by_type(self, use_case, test_user, test_community, test_session):
        """
        测试执行成功 - 只返回 call_for_help 类型事件
        Given: 社区有多种类型的事件
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，只返回 call_for_help 类型的事件
        """
        # Arrange
        # 创建 call_for_help 事件
        call_event = CommunityEvent(
            community_id=test_community.community_id,
            title='求助事件',
            description='测试描述',
            event_type='call_for_help',
            target_user_id=test_user.user_id,
            created_by=test_user.user_id,
            status=1,
            created_at=datetime.datetime.now()
        )
        test_session.add(call_event)

        # 创建 supporting 事件
        support_event = CommunityEvent(
            community_id=test_community.community_id,
            title='支持事件',
            description='测试描述',
            event_type='supporting',
            target_user_id=None,
            created_by=test_user.user_id,
            status=1,
            created_at=datetime.datetime.now()
        )
        test_session.add(support_event)

        # Act
        result = use_case.execute(community_id=test_community.community_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['count'] == 1
        assert result.data['events'][0]['event_type'] == 'call_for_help'


class TestGetCommunityStatsUseCase:
    """GetCommunityStatsUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return GetCommunityStatsUseCase()

    @pytest.fixture
    def test_events(self, test_user, test_community, test_session):
        """创建多个测试事件"""
        events = []
        for i in range(5):
            event = CommunityEvent(
                community_id=test_community.community_id,
                title=f'测试事件{i}',
                description=f'测试描述{i}',
                event_type='call_for_help' if i < 3 else 'supporting',
                target_user_id=test_user.user_id if i < 3 else None,
                created_by=test_user.user_id,
                status=1 if i < 4 else 2,
                created_at=datetime.datetime.now()
            )
            events.append(test_session.add(event))
        return events

    def test_execute_success(self, use_case, test_community, test_events):
        """
        测试执行成功 - 获取社区统计
        Given: 社区有多个事件
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，返回统计数据
        """
        # Act
        result = use_case.execute(community_id=test_community.community_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "获取社区统计成功" in result.message
        assert result.data['active_events'] == 4  # 4个状态为1的事件
        assert result.data['support_count'] == 1  # 1个supporting类型且状态为1的事件

    def test_execute_validation_error_missing_community_id(self, use_case):
        """
        测试验证失败 - 缺少社区ID
        Given: 社区ID为空
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        result = use_case.execute(community_id=None)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "社区ID不能为空" in result.message

    def test_execute_not_found_community_not_exists(self, use_case):
        """
        测试执行失败 - 社区不存在
        Given: 社区ID不存在
        When: 调用 execute 方法
        Then: 返回 NOT_FOUND 状态
        """
        # Arrange
        result = use_case.execute(community_id=99999)

        # Assert
        assert result.status == UseCaseStatus.NOT_FOUND
        assert "社区不存在" in result.message

    def test_execute_success_no_events(self, use_case, test_community):
        """
        测试执行成功 - 没有事件
        Given: 社区没有事件
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，统计数据为0
        """
        # Act
        result = use_case.execute(community_id=test_community.community_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['active_events'] == 0
        assert result.data['support_count'] == 0

    def test_execute_success_only_call_for_help(self, use_case, test_user, test_community, test_session):
        """
        测试执行成功 - 只有一键求助事件
        Given: 社区只有一键求助事件
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，support_count 为 0
        """
        # Arrange
        event = CommunityEvent(
            community_id=test_community.community_id,
            title='求助事件',
            description='测试描述',
            event_type='call_for_help',
            target_user_id=test_user.user_id,
            created_by=test_user.user_id,
            status=1,
            created_at=datetime.datetime.now()
        )
        test_session.add(event)

        # Act
        result = use_case.execute(community_id=test_community.community_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['active_events'] == 1
        assert result.data['support_count'] == 0