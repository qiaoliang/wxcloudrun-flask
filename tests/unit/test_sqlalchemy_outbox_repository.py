import pytest
from datetime import datetime
from app.infrastructure.persistence.sqlalchemy_outbox_repository import SQLAlchemyOutboxRepository
from app.domain.entities.outbox_event_entity import OutboxEventEntity
from app.domain.enums.outbox_status import OutboxStatus

@pytest.fixture
def outbox_repository(test_app):
    """创建 Outbox 仓储实例"""
    with test_app.app_context():
        yield SQLAlchemyOutboxRepository()

def test_save_outbox_event(outbox_repository):
    """测试保存 Outbox 事件"""
    entity = OutboxEventEntity('TestEvent', {'key': 'value'})

    saved = outbox_repository.save(entity)

    assert saved.id is not None
    assert saved.event_type == 'TestEvent'
    assert saved.status == OutboxStatus.PENDING

def test_find_pending_events(outbox_repository):
    """测试查找待处理事件"""
    # 创建一个待处理事件
    entity = OutboxEventEntity('TestEvent', {})
    saved = outbox_repository.save(entity)

    # 查找待处理事件
    pending = outbox_repository.find_pending_events(limit=10)

    assert len(pending) > 0
    assert any(e.id == saved.id for e in pending)

def test_update_status(outbox_repository):
    """测试更新事件状态"""
    entity = OutboxEventEntity('TestEvent', {})
    saved = outbox_repository.save(entity)

    # 更新状态
    outbox_repository.update_status(saved.id, OutboxStatus.PUBLISHED)

    # 验证状态已更新
    updated_events = outbox_repository.find_pending_events()
    assert not any(e.id == saved.id for e in updated_events)
