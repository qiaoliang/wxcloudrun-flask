"""
增强事件总线单元测试

测试原则：
- 使用真实的仓储实现（内存数据库）
- 测试真实行为而非 mock 行为
- 避免过度使用 mock
"""
import pytest
from datetime import datetime

from app.infrastructure.events.enhanced_event_bus import EnhancedEventBus
from app.infrastructure.persistence.sqlalchemy_outbox_repository import SQLAlchemyOutboxRepository
from app.domain.events.checkin_events import CheckinCompletedEvent
from app.domain.entities.outbox_event_entity import OutboxEventEntity
from app.domain.enums.outbox_status import OutboxStatus


class TestEnhancedEventBus:
    """增强事件总线测试类"""

    @pytest.fixture
    def outbox_repo(self, test_session):
        """创建真实的 Outbox 仓储实例"""
        return SQLAlchemyOutboxRepository()

    @pytest.fixture
    def event_bus(self, outbox_repo):
        """创建事件总线实例"""
        return EnhancedEventBus(outbox_repo)

    def test_subscribe_and_publish_sync(self, event_bus):
        """
        测试订阅和同步发布

        Given: 订阅了事件处理器
        When: 发布事件
        Then: 处理器被调用，事件未保存到 Outbox
        """
        # Arrange
        handler_called = []

        def handler(event):
            handler_called.append(event)

        event_bus.subscribe('CheckinCompletedEvent', handler)

        event = CheckinCompletedEvent(1, 100, 10, datetime.now())

        # Act
        event_bus.publish_with_fallback(event)

        # Assert
        assert len(handler_called) == 1
        assert handler_called[0].event_id == event.event_id

        # 验证没有写入 Outbox（因为同步成功）
        pending_events = event_bus._outbox_repo.find_pending_events()
        assert len(pending_events) == 0

    def test_publish_fallback_to_outbox(self, event_bus):
        """
        测试发布失败时降级到 Outbox

        Given: 订阅了一个会失败的处理器
        When: 发布事件
        Then: 事件被保存到 Outbox
        """
        # Arrange
        def failing_handler(event):
            raise Exception('Handler failed')

        event_bus.subscribe('CheckinCompletedEvent', failing_handler)

        # 使用字符串格式的 datetime
        checkin_time = datetime.now()
        event = CheckinCompletedEvent(
            record_id=1,
            user_id=100,
            rule_id=10,
            checkin_time=checkin_time
        )

        # Act - publish_with_fallback 会捕获异常并保存到 Outbox
        event_bus.publish_with_fallback(event)

        # Assert
        # 验证写入了 Outbox
        pending_events = event_bus._outbox_repo.find_pending_events()
        assert len(pending_events) == 1

        saved_event = pending_events[0]
        assert saved_event.event_type == 'CheckinCompletedEvent'
        assert saved_event.status == OutboxStatus.PENDING

    def test_publish_from_outbox(self, event_bus):
        """
        测试从 Outbox 发布事件

        Given: Outbox 中有待处理事件
        When: 从 Outbox 发布事件
        Then: 事件被成功发布
        """
        # Arrange
        handler_called = []

        def handler(event):
            handler_called.append(event)

        event_bus.subscribe('CheckinCompletedEvent', handler)

        # 创建一个模拟的 OutboxEvent
        outbox_event = OutboxEventEntity('CheckinCompletedEvent', {
            'event_id': 'test-id',
            'aggregate_id': 1,
            'data': {'record_id': 1, 'user_id': 100, 'rule_id': 10, 'checkin_time': datetime.now().isoformat()},
            'occurred_on': '2026-01-18T10:00:00'
        })

        # Act
        success = event_bus.publish_from_outbox(outbox_event)

        # Assert
        assert success is True
        assert len(handler_called) == 1

    def test_multiple_handlers(self, event_bus):
        """
        测试多个处理器

        Given: 订阅了多个处理器
        When: 发布事件
        Then: 所有处理器都被调用
        """
        # Arrange
        handler1_called = []
        handler2_called = []

        def handler1(event):
            handler1_called.append(event)

        def handler2(event):
            handler2_called.append(event)

        event_bus.subscribe('CheckinCompletedEvent', handler1)
        event_bus.subscribe('CheckinCompletedEvent', handler2)

        event = CheckinCompletedEvent(1, 100, 10, datetime.now())

        # Act
        event_bus.publish_with_fallback(event)

        # Assert
        assert len(handler1_called) == 1
        assert len(handler2_called) == 1

    def test_unsubscribe(self, event_bus):
        """
        测试取消订阅

        Given: 订阅了处理器
        When: 取消订阅后发布事件
        Then: 处理器不被调用
        """
        # Arrange
        handler_called = []

        def handler(event):
            handler_called.append(event)

        event_bus.subscribe('CheckinCompletedEvent', handler)
        event_bus.unsubscribe('CheckinCompletedEvent', handler)

        event = CheckinCompletedEvent(1, 100, 10, datetime.now())

        # Act
        event_bus.publish_with_fallback(event)

        # Assert
        assert len(handler_called) == 0

    def test_no_handlers(self, event_bus):
        """
        测试没有处理器的情况

        Given: 没有订阅任何处理器
        When: 发布事件
        Then: 事件被忽略，不保存到 Outbox
        """
        # Arrange
        event = CheckinCompletedEvent(1, 100, 10, datetime.now())

        # Act
        event_bus.publish_with_fallback(event)

        # Assert
        pending_events = event_bus._outbox_repo.find_pending_events()
        assert len(pending_events) == 0

    def test_publish_from_outbox_no_handlers(self, event_bus):
        """
        测试从 Outbox 发布事件但没有处理器

        Given: Outbox 中有待处理事件，但没有订阅处理器
        When: 从 Outbox 发布事件
        Then: 返回 False
        """
        # Arrange
        outbox_event = OutboxEventEntity('CheckinCompletedEvent', {
            'event_id': 'test-id',
            'aggregate_id': 1,
            'data': {'record_id': 1, 'user_id': 100, 'rule_id': 10},
            'occurred_on': '2026-01-18T10:00:00'
        })

        # Act
        success = event_bus.publish_from_outbox(outbox_event)

        # Assert
        assert success is False

    def test_publish_from_outbox_handler_fails(self, event_bus, test_session):
        """
        测试从 Outbox 发布事件时处理器失败

        Given: Outbox 中有待处理事件，但处理器会失败
        When: 从 Outbox 发布事件
        Then: 返回 False，事件重试次数增加
        """
        # Arrange
        def failing_handler(event):
            raise Exception('Handler failed')

        event_bus.subscribe('CheckinCompletedEvent', failing_handler)

        outbox_event = OutboxEventEntity('CheckinCompletedEvent', {
            'event_id': 'test-id',
            'aggregate_id': 1,
            'data': {'record_id': 1, 'user_id': 100, 'rule_id': 10},
            'occurred_on': '2026-01-18T10:00:00'
        })
        outbox_event.id = 1

        # Act
        success = event_bus.publish_from_outbox(outbox_event)

        # Assert
        assert success is False
        assert outbox_event.retry_count > 0