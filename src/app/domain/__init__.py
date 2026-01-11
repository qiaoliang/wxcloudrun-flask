"""
领域层导出

包含领域实体、值对象、领域事件和仓储接口
"""
from .entities import (
    UserEntity,
    CommunityEntity,
    CheckinRuleEntity,
    CommunityCheckinRuleEntity,
    CheckinRecordEntity,
    CommunityEventEntity,
)
from .value_objects import (
    Role,
    RoleType,
    PhoneNumber,
    Frequency,
    FrequencyType,
    TimeSlot,
    TimeSlotType,
    CommunityEventType,
    EventType,
    CommunityEventStatus,
    EventStatus,
)

__all__ = [
    # 实体
    'UserEntity',
    'CommunityEntity',
    'CheckinRuleEntity',
    'CommunityCheckinRuleEntity',
    'CheckinRecordEntity',
    'CommunityEventEntity',
    # 值对象
    'Role',
    'RoleType',
    'PhoneNumber',
    'Frequency',
    'FrequencyType',
    'TimeSlot',
    'TimeSlotType',
    'CommunityEventType',
    'EventType',
    'CommunityEventStatus',
    'EventStatus',
]