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


def test_outbox_status_comparison():
    """测试 OutboxStatus 枚举比较"""
    assert OutboxStatus.PENDING == OutboxStatus.PENDING
    assert OutboxStatus.PENDING != OutboxStatus.PUBLISHED


def test_outbox_status_from_string():
    """测试从字符串创建 OutboxStatus"""
    assert OutboxStatus('pending') == OutboxStatus.PENDING
    assert OutboxStatus('published') == OutboxStatus.PUBLISHED
    assert OutboxStatus('failed') == OutboxStatus.FAILED


def test_outbox_status_invalid_string():
    """测试无效字符串创建 OutboxStatus"""
    with pytest.raises(ValueError):
        OutboxStatus('invalid_status')
