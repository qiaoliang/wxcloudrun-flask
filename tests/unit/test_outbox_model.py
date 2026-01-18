"""
测试 OutboxEvent ORM 模型

测试范围：
- OutboxEvent 模型的基本创建
- 字段属性验证
"""
import pytest
from datetime import datetime
from src.database.flask_models import OutboxEvent

def test_outbox_model_creation():
    """测试 OutboxEvent ORM 模型创建"""
    event = OutboxEvent(
        event_type='TestEvent',
        payload={'key': 'value'},
        status='pending',
        retry_count=0,
        created_at=datetime.now(),
        next_retry_at=datetime.now()
    )

    assert event.event_type == 'TestEvent'
    assert event.payload == {'key': 'value'}
    assert event.status == 'pending'
    assert event.retry_count == 0
