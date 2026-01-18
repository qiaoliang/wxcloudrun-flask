import pytest
from abc import ABC
from app.domain.repositories.outbox_repository import OutboxRepository
from app.domain.entities.outbox_event_entity import OutboxEventEntity

def test_outbox_repository_is_abstract():
    """测试 OutboxRepository 是抽象类"""
    assert issubclass(OutboxRepository, ABC)

def test_outbox_repository_has_required_methods():
    """测试 OutboxRepository 有必需的方法"""
    assert hasattr(OutboxRepository, 'save')
    assert hasattr(OutboxRepository, 'find_pending_events')
    assert hasattr(OutboxRepository, 'update_status')
