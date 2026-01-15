"""
事件处理器注册模块

负责在应用启动时注册所有事件处理器
"""
from app.domain.events.event_bus import event_bus
from app.domain.handlers.user_event_handlers import (
    UserCreatedEventHandler,
    UserJoinedCommunityEventHandler,
    UserLeftCommunityEventHandler,
    UserProfileUpdatedEventHandler,
    UserPasswordChangedEventHandler,
    UserAvatarUpdatedEventHandler,
    UserStatusChangedEventHandler,
    UserRoleChangedEventHandler
)
from app.domain.handlers.community_event_handlers import (
    CommunityCreatedEventHandler,
    CommunityUpdatedEventHandler,
    CommunityDeletedEventHandler,
    CommunityMemberAddedEventHandler,
    CommunityMemberRemovedEventHandler,
    CommunityManagerChangedEventHandler,
    CommunityStatusChangedEventHandler,
    CommunitySettingsUpdatedEventHandler,
    EventCreatedEventHandler,
    EventClosedEventHandler,
    EventCancelledEventHandler,
    EventSupportedEventHandler,
    EventLocationUpdatedEventHandler,
    EventMessageAddedEventHandler,
    EventStatusChangedEventHandler,
    EventDetailsViewedEventHandler,
    CommunityStatsRetrievedEventHandler
)
from app.domain.handlers.checkin_event_handlers import (
    CheckinCompletedEventHandler,
    CheckinMissedEventHandler,
    CheckinCancelledEventHandler,
    CheckinRuleCreatedEventHandler,
    CheckinRuleUpdatedEventHandler,
    CheckinRuleDeletedEventHandler,
    CheckinRuleEnabledEventHandler,
    CheckinRuleDisabledEventHandler
)


def register_all_event_handlers():
    """
    注册所有事件处理器到事件总线

    此函数应该在应用启动时调用
    """
    # 注册用户事件处理器
    event_bus.subscribe(UserCreatedEventHandler())
    event_bus.subscribe(UserJoinedCommunityEventHandler())
    event_bus.subscribe(UserLeftCommunityEventHandler())
    event_bus.subscribe(UserProfileUpdatedEventHandler())
    event_bus.subscribe(UserPasswordChangedEventHandler())
    event_bus.subscribe(UserAvatarUpdatedEventHandler())
    event_bus.subscribe(UserStatusChangedEventHandler())
    event_bus.subscribe(UserRoleChangedEventHandler())

    # 注册社区事件处理器
    event_bus.subscribe(CommunityCreatedEventHandler())
    event_bus.subscribe(CommunityUpdatedEventHandler())
    event_bus.subscribe(CommunityDeletedEventHandler())
    event_bus.subscribe(CommunityMemberAddedEventHandler())
    event_bus.subscribe(CommunityMemberRemovedEventHandler())
    event_bus.subscribe(CommunityManagerChangedEventHandler())
    event_bus.subscribe(CommunityStatusChangedEventHandler())
    event_bus.subscribe(CommunitySettingsUpdatedEventHandler())

    # 注册事件事件处理器
    event_bus.subscribe(EventCreatedEventHandler())
    event_bus.subscribe(EventClosedEventHandler())
    event_bus.subscribe(EventCancelledEventHandler())
    event_bus.subscribe(EventSupportedEventHandler())
    event_bus.subscribe(EventLocationUpdatedEventHandler())
    event_bus.subscribe(EventMessageAddedEventHandler())
    event_bus.subscribe(EventStatusChangedEventHandler())
    event_bus.subscribe(EventDetailsViewedEventHandler())
    event_bus.subscribe(CommunityStatsRetrievedEventHandler())

    # 注册打卡事件处理器
    event_bus.subscribe(CheckinCompletedEventHandler())
    event_bus.subscribe(CheckinMissedEventHandler())
    event_bus.subscribe(CheckinCancelledEventHandler())
    event_bus.subscribe(CheckinRuleCreatedEventHandler())
    event_bus.subscribe(CheckinRuleUpdatedEventHandler())
    event_bus.subscribe(CheckinRuleDeletedEventHandler())
    event_bus.subscribe(CheckinRuleEnabledEventHandler())
    event_bus.subscribe(CheckinRuleDisabledEventHandler())


def get_event_handler_count():
    """
    获取已注册的事件处理器数量

    Returns:
        dict: 各类型事件的处理器数量统计
    """
    from app.domain.events.user_events import (
        UserCreatedEvent,
        UserJoinedCommunityEvent,
        UserLeftCommunityEvent,
        UserProfileUpdatedEvent,
        UserPasswordChangedEvent,
        UserAvatarUpdatedEvent,
        UserStatusChangedEvent,
        UserRoleChangedEvent
    )
    from app.domain.events.community_events import (
        CommunityCreatedEvent,
        CommunityUpdatedEvent,
        CommunityDeletedEvent,
        CommunityMemberAddedEvent,
        CommunityMemberRemovedEvent,
        CommunityManagerChangedEvent,
        CommunityStatusChangedEvent,
        CommunitySettingsUpdatedEvent,
        EventCreatedEvent,
        EventClosedEvent,
        EventCancelledEvent,
        EventSupportedEvent,
        EventLocationUpdatedEvent,
        EventMessageAddedEvent,
        EventStatusChangedEvent,
        EventDetailsViewedEvent,
        CommunityStatsRetrievedEvent
    )
    from app.domain.events.checkin_events import (
        CheckinCompletedEvent,
        CheckinMissedEvent,
        CheckinCancelledEvent,
        CheckinRuleCreatedEvent,
        CheckinRuleUpdatedEvent,
        CheckinRuleDeletedEvent,
        CheckinRuleEnabledEvent,
        CheckinRuleDisabledEvent
    )

    return {
        'user_events': {
            'UserCreatedEvent': event_bus.get_handler_count(UserCreatedEvent),
            'UserJoinedCommunityEvent': event_bus.get_handler_count(UserJoinedCommunityEvent),
            'UserLeftCommunityEvent': event_bus.get_handler_count(UserLeftCommunityEvent),
            'UserProfileUpdatedEvent': event_bus.get_handler_count(UserProfileUpdatedEvent),
            'UserPasswordChangedEvent': event_bus.get_handler_count(UserPasswordChangedEvent),
            'UserAvatarUpdatedEvent': event_bus.get_handler_count(UserAvatarUpdatedEvent),
            'UserStatusChangedEvent': event_bus.get_handler_count(UserStatusChangedEvent),
            'UserRoleChangedEvent': event_bus.get_handler_count(UserRoleChangedEvent),
        },
        'community_events': {
            'CommunityCreatedEvent': event_bus.get_handler_count(CommunityCreatedEvent),
            'CommunityUpdatedEvent': event_bus.get_handler_count(CommunityUpdatedEvent),
            'CommunityDeletedEvent': event_bus.get_handler_count(CommunityDeletedEvent),
            'CommunityMemberAddedEvent': event_bus.get_handler_count(CommunityMemberAddedEvent),
            'CommunityMemberRemovedEvent': event_bus.get_handler_count(CommunityMemberRemovedEvent),
            'CommunityManagerChangedEvent': event_bus.get_handler_count(CommunityManagerChangedEvent),
            'CommunityStatusChangedEvent': event_bus.get_handler_count(CommunityStatusChangedEvent),
            'CommunitySettingsUpdatedEvent': event_bus.get_handler_count(CommunitySettingsUpdatedEvent),
            'EventCreatedEvent': event_bus.get_handler_count(EventCreatedEvent),
            'EventClosedEvent': event_bus.get_handler_count(EventClosedEvent),
            'EventCancelledEvent': event_bus.get_handler_count(EventCancelledEvent),
            'EventSupportedEvent': event_bus.get_handler_count(EventSupportedEvent),
            'EventLocationUpdatedEvent': event_bus.get_handler_count(EventLocationUpdatedEvent),
            'EventMessageAddedEvent': event_bus.get_handler_count(EventMessageAddedEvent),
            'EventStatusChangedEvent': event_bus.get_handler_count(EventStatusChangedEvent),
            'EventDetailsViewedEvent': event_bus.get_handler_count(EventDetailsViewedEvent),
            'CommunityStatsRetrievedEvent': event_bus.get_handler_count(CommunityStatsRetrievedEvent),
        },
        'checkin_events': {
            'CheckinCompletedEvent': event_bus.get_handler_count(CheckinCompletedEvent),
            'CheckinMissedEvent': event_bus.get_handler_count(CheckinMissedEvent),
            'CheckinCancelledEvent': event_bus.get_handler_count(CheckinCancelledEvent),
            'CheckinRuleCreatedEvent': event_bus.get_handler_count(CheckinRuleCreatedEvent),
            'CheckinRuleUpdatedEvent': event_bus.get_handler_count(CheckinRuleUpdatedEvent),
            'CheckinRuleDeletedEvent': event_bus.get_handler_count(CheckinRuleDeletedEvent),
            'CheckinRuleEnabledEvent': event_bus.get_handler_count(CheckinRuleEnabledEvent),
            'CheckinRuleDisabledEvent': event_bus.get_handler_count(CheckinRuleDisabledEvent),
        }
    }