import pytest
from unittest.mock import Mock
from app.infrastructure.events.enhanced_event_bus import EnhancedEventBus
from app.domain.events.checkin_events import CheckinCompletedEvent
from app.domain.entities.outbox_event_entity import OutboxEventEntity


def test_subscribe_and_publish_sync():
    """测试订阅和同步发布"""
    mock_outbox_repo = Mock()
    event_bus = EnhancedEventBus(mock_outbox_repo)

    handler = Mock()
    event_bus.subscribe('CheckinCompletedEvent', handler)

    from datetime import datetime
    event = CheckinCompletedEvent(1, 100, 10, datetime.now())
    event_bus.publish_with_fallback(event)

    # 验证处理器被调用
    handler.assert_called_once()
    # 验证没有写入 Outbox（因为同步成功）
    mock_outbox_repo.save.assert_not_called()


def test_publish_fallback_to_outbox():
    """测试发布失败时降级到 Outbox"""
    mock_outbox_repo = Mock()
    event_bus = EnhancedEventBus(mock_outbox_repo)

    # 创建一个会失败的处理器
    handler = Mock(side_effect=Exception('Handler failed'))
    event_bus.subscribe('CheckinCompletedEvent', handler)

    from datetime import datetime
    event = CheckinCompletedEvent(1, 100, 10, datetime.now())
    event_bus.publish_with_fallback(event)

    # 验证写入了 Outbox
    mock_outbox_repo.save.assert_called_once()
    saved_event = mock_outbox_repo.save.call_args[0][0]
    assert saved_event.event_type == 'CheckinCompletedEvent'


def test_publish_from_outbox():
    """测试从 Outbox 发布事件"""
    mock_outbox_repo = Mock()
    event_bus = EnhancedEventBus(mock_outbox_repo)

    handler = Mock()
    event_bus.subscribe('CheckinCompletedEvent', handler)

    # 创建一个模拟的 OutboxEvent
    outbox_event = OutboxEventEntity('CheckinCompletedEvent', {
        'event_id': 'test-id',
        'aggregate_id': 1,
        'data': {'user_id': 100, 'rule_id': 10},
        'occurred_on': '2026-01-18T10:00:00'
    })

    success = event_bus.publish_from_outbox(outbox_event)

    assert success is True
    handler.assert_called_once()
