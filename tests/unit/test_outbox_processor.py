# tests/unit/test_outbox_processor.py
import pytest
import time
from unittest.mock import Mock, MagicMock
from app.infrastructure.events.outbox_processor import OutboxProcessor
from app.domain.entities.outbox_event_entity import OutboxEventEntity
from app.domain.enums.outbox_status import OutboxStatus

def test_outbox_processor_start_stop():
    """测试处理器启动和停止"""
    mock_outbox_repo = Mock()
    mock_outbox_repo.find_pending_events.return_value = []
    mock_event_bus = Mock()

    processor = OutboxProcessor(
        mock_outbox_repo,
        mock_event_bus,
        interval_seconds=1
    )

    processor.start()
    assert processor._running is True
    assert processor._thread is not None

    processor.stop()
    assert processor._running is False

def test_outbox_processor_processes_events():
    """测试处理器处理事件"""
    # 创建模拟事件
    event1 = OutboxEventEntity('TestEvent', {'id': 1})
    event1.id = 1
    event2 = OutboxEventEntity('TestEvent', {'id': 2})
    event2.id = 2

    mock_outbox_repo = Mock()
    mock_outbox_repo.find_pending_events.return_value = [event1, event2]

    mock_event_bus = Mock()
    mock_event_bus.publish_from_outbox.return_value = True

    processor = OutboxProcessor(
        mock_outbox_repo,
        mock_event_bus,
        interval_seconds=1
    )

    # 手动触发一次处理
    processor._process_batch()

    # 验证处理了两个事件
    assert mock_event_bus.publish_from_outbox.call_count == 2
    assert mock_outbox_repo.update_status.call_count == 2

def test_outbox_processor_retry_logic():
    """测试重试逻辑"""
    event = OutboxEventEntity('TestEvent', {})
    event.id = 1

    mock_outbox_repo = Mock()
    mock_outbox_repo.find_pending_events.return_value = [event]

    mock_event_bus = Mock()
    mock_event_bus.publish_from_outbox.return_value = False  # 发布失败

    processor = OutboxProcessor(
        mock_outbox_repo,
        mock_event_bus,
        interval_seconds=1
    )

    processor._process_batch()

    # 验证计算了下一次重试时间
    assert event.retry_count > 0
    # 验证没有标记为已发布（PUBLISHED）
    if mock_outbox_repo.update_status.called:
        for call in mock_outbox_repo.update_status.call_args_list:
            # 确保没有将状态更新为 PUBLISHED
            assert call[0][1] != OutboxStatus.PUBLISHED
