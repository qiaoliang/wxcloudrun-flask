"""
领域事件

领域事件是领域中发生的重要事情，用于解耦聚合根之间的交互。
"""
from .domain_event import DomainEvent
from .event_bus import EventBus
from .user_events import UserCreatedEvent, UserJoinedCommunityEvent, UserLeftCommunityEvent
from .community_events import CommunityCreatedEvent, CommunityMemberAddedEvent
from .checkin_events import CheckinCompletedEvent, CheckinMissedEvent
from .event_handlers import UserEventHandler, CommunityEventHandler, CheckinEventHandler

__all__ = [
    'DomainEvent',
    'EventBus',
    'UserCreatedEvent',
    'UserJoinedCommunityEvent',
    'UserLeftCommunityEvent',
    'CommunityCreatedEvent',
    'CommunityMemberAddedEvent',
    'CheckinCompletedEvent',
    'CheckinMissedEvent',
    'UserEventHandler',
    'CommunityEventHandler',
    'CheckinEventHandler',
]