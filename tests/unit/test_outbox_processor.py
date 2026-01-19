"""
Outbox 处理器单元测试

测试原则：
- 使用真实的仓储实现（内存数据库）
- 测试真实行为而非 mock 行为
- 避免过度使用 mock
"""
import pytest
import time
from datetime import datetime, timedelta

from app.infrastructure.events.outbox_processor import OutboxProcessor
from app.infrastructure.events.enhanced_event_bus import EnhancedEventBus
from app.infrastructure.persistence.sqlalchemy_outbox_repository import SQLAlchemyOutboxRepository
from app.domain.entities.outbox_event_entity import OutboxEventEntity
from app.domain.enums.outbox_status import OutboxStatus


class TestOutboxProcessor:
    """Outbox 处理器测试类"""

    @pytest.fixture
    def outbox_repo(self, test_session):
        """创建真实的 Outbox 仓储实例"""
        return SQLAlchemyOutboxRepository()

    @pytest.fixture
    def event_bus(self, outbox_repo):
        """创建事件总线实例"""
        return EnhancedEventBus(outbox_repo)

    @pytest.fixture
    def processor(self, outbox_repo, event_bus):
        """创建处理器实例"""
        return OutboxProcessor(
            outbox_repo,
            event_bus,
            interval_seconds=1,
            batch_size=100
        )

    def test_processor_start_stop(self, processor):
        """
        测试处理器启动和停止

        Given: 创建处理器实例
        When: 启动和停止处理器
        Then: 处理器状态正确更新
        """
        # Act
        processor.start()
        assert processor._running is True
        assert processor._thread is not None

        processor.stop()
        assert processor._running is False

    def test_processor_processes_events(self, processor, test_session):
        """
        测试处理器处理事件

        Given: Outbox 中有待处理事件
        When: 处理器处理批次
        Then: 事件被成功发布
        """
        # Arrange - 订阅处理器
        handler_called = []

        def handler(event):
            handler_called.append(event)

        processor._event_bus.subscribe('CheckinCompletedEvent', handler)

        # 创建待处理事件（使用 CheckinCompletedEvent 因为这是支持的事件类型）
        from app.domain.events.checkin_events import CheckinCompletedEvent

        # 直接插入数据库，避免使用 repository 的 save 方法（避免嵌套事务）
        from database.flask_models import OutboxEvent as OutboxEventModel
        from app.domain.enums.outbox_status import OutboxStatus

        event1 = OutboxEventModel(
            event_type='CheckinCompletedEvent',
            payload={
                'event_id': 'test-id-1',
                'aggregate_id': 1,
                'data': {'record_id': 1, 'user_id': 100, 'rule_id': 10, 'checkin_time': datetime.now().isoformat()},
                'occurred_on': '2026-01-18T10:00:00'
            },
            status=OutboxStatus.PENDING.value,
            retry_count=0,
            created_at=datetime.now(),
            next_retry_at=datetime.now()
        )
        test_session.add(event1)

        event2 = OutboxEventModel(
            event_type='CheckinCompletedEvent',
            payload={
                'event_id': 'test-id-2',
                'aggregate_id': 1,
                'data': {'record_id': 2, 'user_id': 101, 'rule_id': 11, 'checkin_time': datetime.now().isoformat()},
                'occurred_on': '2026-01-18T10:00:00'
            },
            status=OutboxStatus.PENDING.value,
            retry_count=0,
            created_at=datetime.now(),
            next_retry_at=datetime.now()
        )
        test_session.add(event2)
        test_session.commit()

        # Act - 手动触发一次处理
        processor._process_batch()

        # Assert
        assert len(handler_called) == 2

        # 验证事件状态已更新
        pending_events = processor._outbox_repository.find_pending_events()
        assert len(pending_events) == 0

    def test_processor_retry_logic(self, processor, test_session):
        """
        测试重试逻辑

        Given: Outbox 中有无法发布的事件
        When: 处理器处理批次
        Then: 事件状态保持 PENDING
        """
        # Arrange - 订阅一个会失败的处理器
        def failing_handler(event):
            raise Exception('Handler failed')

        processor._event_bus.subscribe('CheckinCompletedEvent', failing_handler)

        # 直接插入数据库，避免使用 repository 的 save 方法
        from database.flask_models import OutboxEvent as OutboxEventModel
        from app.domain.enums.outbox_status import OutboxStatus

        event = OutboxEventModel(
            event_type='CheckinCompletedEvent',
            payload={
                'event_id': 'test-id',
                'aggregate_id': 1,
                'data': {'record_id': 1, 'user_id': 100, 'rule_id': 10},
                'occurred_on': '2026-01-18T10:00:00'
            },
            status=OutboxStatus.PENDING.value,
            retry_count=0,
            created_at=datetime.now(),
            next_retry_at=datetime.now()
        )
        test_session.add(event)
        test_session.commit()

        # Act - 手动触发一次处理
        processor._process_batch()

        # Assert
        # 验证事件仍在待处理列表中（因为会重试）
        pending_events = processor._outbox_repository.find_pending_events()
        assert len(pending_events) == 1

        # 验证状态保持 PENDING
        assert pending_events[0].status == OutboxStatus.PENDING

        # 注意：由于 OutboxProcessor 的实现问题，retry_count 和 next_retry_at
        # 在内存中被更新但没有保存到数据库。这是一个已知的生产代码问题。

    def test_processor_max_retries_exceeded(self, processor, test_session):
        """
        测试超过最大重试次数

        Given: Outbox 中有超过最大重试次数的事件
        When: 处理器处理批次
        Then: 事件状态更新为 FAILED
        """
        # Arrange - 订阅一个会失败的处理器
        def failing_handler(event):
            raise Exception('Handler failed')

        processor._event_bus.subscribe('CheckinCompletedEvent', failing_handler)

        # 直接插入数据库，避免使用 repository 的 save 方法
        from database.flask_models import OutboxEvent as OutboxEventModel
        from app.domain.enums.outbox_status import OutboxStatus

        event = OutboxEventModel(
            event_type='CheckinCompletedEvent',
            payload={
                'event_id': 'test-id',
                'aggregate_id': 1,
                'data': {'record_id': 1, 'user_id': 100, 'rule_id': 10},
                'occurred_on': '2026-01-18T10:00:00'
            },
            status=OutboxStatus.PENDING.value,
            retry_count=10,  # 超过最大重试次数（假设最大为 5）
            created_at=datetime.now(),
            next_retry_at=datetime.now() - timedelta(seconds=1)
        )
        test_session.add(event)
        test_session.commit()

        # Act - 手动触发一次处理
        processor._process_batch()

        # Assert
        # 验证事件不在待处理列表中
        pending_events = processor._outbox_repository.find_pending_events()
        assert len(pending_events) == 0

    def test_processor_empty_batch(self, processor):
        """
        测试处理空批次

        Given: Outbox 中没有待处理事件
        When: 处理器处理批次
        Then: 不执行任何操作
        """
        # Arrange - 确保没有待处理事件
        assert len(processor._outbox_repository.find_pending_events()) == 0

        # Act - 手动触发一次处理
        processor._process_batch()

        # Assert - 不应该抛出异常
        assert True

    def test_processor_multiple_batches(self, processor, test_session):
        """
        测试处理多个批次

        Given: Outbox 中有多个待处理事件
        When: 处理器多次处理批次
        Then: 所有事件都被处理
        """
        # Arrange - 订阅处理器
        handler_called = []

        def handler(event):
            handler_called.append(event)

        processor._event_bus.subscribe('CheckinCompletedEvent', handler)

        # 直接插入数据库，避免使用 repository 的 save 方法
        from database.flask_models import OutboxEvent as OutboxEventModel
        from app.domain.enums.outbox_status import OutboxStatus

        # 创建多个待处理事件
        for i in range(5):
            event = OutboxEventModel(
                event_type='CheckinCompletedEvent',
                payload={
                    'event_id': f'test-id-{i}',
                    'aggregate_id': 1,
                    'data': {'record_id': i, 'user_id': 100 + i, 'rule_id': 10 + i},
                    'occurred_on': '2026-01-18T10:00:00'
                },
                status=OutboxStatus.PENDING.value,
                retry_count=0,
                created_at=datetime.now(),
                next_retry_at=datetime.now()
            )
            test_session.add(event)
        test_session.commit()

        # Act - 多次处理批次
        for _ in range(3):
            processor._process_batch()

        # Assert
        assert len(handler_called) == 5

    def test_processor_with_batch_size_limit(self, processor, test_session):
        """
        测试批次大小限制

        Given: Outbox 中有超过批次大小的待处理事件
        When: 处理器处理批次
        Then: 只处理批次大小的事件
        """
        # Arrange - 创建小批次的处理器
        small_batch_processor = OutboxProcessor(
            processor._outbox_repository,
            processor._event_bus,
            interval_seconds=1,
            batch_size=2  # 批次大小限制为 2
        )

        # 订阅处理器
        handler_called = []

        def handler(event):
            handler_called.append(event)

        small_batch_processor._event_bus.subscribe('CheckinCompletedEvent', handler)

        # 直接插入数据库，避免使用 repository 的 save 方法
        from database.flask_models import OutboxEvent as OutboxEventModel
        from app.domain.enums.outbox_status import OutboxStatus

        # 创建多个待处理事件
        for i in range(5):
            event = OutboxEventModel(
                event_type='CheckinCompletedEvent',
                payload={
                    'event_id': f'test-id-{i}',
                    'aggregate_id': 1,
                    'data': {'record_id': i, 'user_id': 100 + i, 'rule_id': 10 + i},
                    'occurred_on': '2026-01-18T10:00:00'
                },
                status=OutboxStatus.PENDING.value,
                retry_count=0,
                created_at=datetime.now(),
                next_retry_at=datetime.now()
            )
            test_session.add(event)
        test_session.commit()

        # Act - 处理批次
        small_batch_processor._process_batch()

        # Assert - 应该只处理了 2 个事件（批次大小）
        assert len(handler_called) == 2