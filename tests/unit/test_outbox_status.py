import pytest
from app.domain.enums.outbox_status import OutboxStatus


def test_outbox_status_enum():
    """测试 OutboxStatus 枚举"""
    assert OutboxStatus.PENDING.value == 'pending'
    assert OutboxStatus.PUBLISHED.value == 'published'
    assert OutboxStatus.FAILED.value == 'failed'


def test_outbox_status_enum_members():
    """测试 OutboxStatus 枚举成员"""
    assert len(OutboxStatus) == 3
    assert OutboxStatus.PENDING in OutboxStatus
    assert OutboxStatus.PUBLISHED in OutboxStatus
    assert OutboxStatus.FAILED in OutboxStatus


def test_outbox_status_enum_values():
    """测试 OutboxStatus 枚举值唯一性"""
    values = [status.value for status in OutboxStatus]
    assert len(values) == len(set(values)), "OutboxStatus 枚举值应该是唯一的"
