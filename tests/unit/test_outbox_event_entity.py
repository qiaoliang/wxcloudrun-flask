import pytest
from datetime import datetime, timedelta
from app.domain.entities.outbox_event_entity import OutboxEventEntity
from app.domain.enums.outbox_status import OutboxStatus

def test_outbox_event_creation():
    """测试 OutboxEvent 实体创建"""
    entity = OutboxEventEntity('TestEvent', {'key': 'value'})

    assert entity.event_type == 'TestEvent'
    assert entity.payload == {'key': 'value'}
    assert entity.status == OutboxStatus.PENDING
    assert entity.retry_count == 0
    assert entity.created_at is not None
    assert entity.next_retry_at is not None

def test_mark_as_published():
    """测试标记为已发布"""
    entity = OutboxEventEntity('TestEvent', {})
    entity.mark_as_published()

    assert entity.status == OutboxStatus.PUBLISHED
    assert entity.published_at is not None

def test_calculate_next_retry():
    """测试计算下次重试时间（指数退避）"""
    entity = OutboxEventEntity('TestEvent', {})

    # 第一次重试：1秒
    entity.calculate_next_retry()
    assert entity.retry_count == 1
    expected_time = datetime.now() + timedelta(seconds=1)
    assert abs((entity.next_retry_at - expected_time).total_seconds()) < 1

    # 第五次重试：最多60秒
    entity.retry_count = 4
    entity.calculate_next_retry()
    assert entity.retry_count == 5
    expected_time = datetime.now() + timedelta(seconds=16)  # 2^4 = 16
    assert abs((entity.next_retry_at - expected_time).total_seconds()) < 1

def test_should_retry():
    """测试是否应该重试"""
    entity = OutboxEventEntity('TestEvent', {})

    assert entity.should_retry() is True

    entity.retry_count = 4
    assert entity.should_retry() is True

    entity.retry_count = 5
    assert entity.should_retry() is False
