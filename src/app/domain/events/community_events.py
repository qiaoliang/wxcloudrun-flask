"""
社区相关领域事件
"""
from app.domain.events.domain_event import DomainEvent


# ==================== 社区领域事件 ====================

class CommunityCreatedEvent(DomainEvent):
    """社区创建事件"""

    def __init__(self, community_id: int, creator_id: int, community_name: str):
        """
        初始化社区创建事件

        Args:
            community_id: 社区ID
            creator_id: 创建者ID
            community_name: 社区名称
        """
        super().__init__(community_id, {
            'community_id': community_id,
            'creator_id': creator_id,
            'community_name': community_name
        })


class CommunityUpdatedEvent(DomainEvent):
    """社区更新事件"""

    def __init__(self, community_id: int, updater_id: int, updated_fields: dict):
        """
        初始化社区更新事件

        Args:
            community_id: 社区ID
            updater_id: 更新者ID
            updated_fields: 更新的字段
        """
        super().__init__(community_id, {
            'community_id': community_id,
            'updater_id': updater_id,
            'updated_fields': updated_fields
        })


class CommunityDeletedEvent(DomainEvent):
    """社区删除事件"""

    def __init__(self, community_id: int, deleter_id: int, community_name: str):
        """
        初始化社区删除事件

        Args:
            community_id: 社区ID
            deleter_id: 删除者ID
            community_name: 社区名称
        """
        super().__init__(community_id, {
            'community_id': community_id,
            'deleter_id': deleter_id,
            'community_name': community_name
        })


class CommunityMemberAddedEvent(DomainEvent):
    """社区成员添加事件"""

    def __init__(self, community_id: int, user_id: int, role: int):
        """
        初始化社区成员添加事件

        Args:
            community_id: 社区ID
            user_id: 用户ID
            role: 角色
        """
        super().__init__(community_id, {
            'community_id': community_id,
            'user_id': user_id,
            'role': role
        })


class CommunityMemberRemovedEvent(DomainEvent):
    """社区成员移除事件"""

    def __init__(self, community_id: int, user_id: int, role: int):
        """
        初始化社区成员移除事件

        Args:
            community_id: 社区ID
            user_id: 用户ID
            role: 角色
        """
        super().__init__(community_id, {
            'community_id': community_id,
            'user_id': user_id,
            'role': role
        })


class CommunityManagerChangedEvent(DomainEvent):
    """社区主管变更事件"""

    def __init__(self, community_id: int, old_manager_id: int, new_manager_id: int):
        """
        初始化社区主管变更事件

        Args:
            community_id: 社区ID
            old_manager_id: 旧主管ID
            new_manager_id: 新主管ID
        """
        super().__init__(community_id, {
            'community_id': community_id,
            'old_manager_id': old_manager_id,
            'new_manager_id': new_manager_id
        })


class CommunityStatusChangedEvent(DomainEvent):
    """社区状态变更事件"""

    def __init__(self, community_id: int, old_status: int, new_status: int, operator_id: int):
        """
        初始化社区状态变更事件

        Args:
            community_id: 社区ID
            old_status: 旧状态
            new_status: 新状态
            operator_id: 操作者ID
        """
        super().__init__(community_id, {
            'community_id': community_id,
            'old_status': old_status,
            'new_status': new_status,
            'operator_id': operator_id
        })


class CommunitySettingsUpdatedEvent(DomainEvent):
    """社区设置更新事件"""

    def __init__(self, community_id: int, settings: dict, operator_id: int):
        """
        初始化社区设置更新事件

        Args:
            community_id: 社区ID
            settings: 设置内容
            operator_id: 操作者ID
        """
        super().__init__(community_id, {
            'community_id': community_id,
            'settings': settings,
            'operator_id': operator_id
        })


# ==================== 社区事件领域事件 ====================

class EventCreatedEvent(DomainEvent):
    """事件创建领域事件"""

    def __init__(self, event_id: int, community_id: int, creator_id: int,
                 event_type: str, title: str, target_user_id: int = None):
        """
        初始化事件创建事件

        Args:
            event_id: 事件ID
            community_id: 社区ID
            creator_id: 创建者ID
            event_type: 事件类型
            title: 事件标题
            target_user_id: 目标用户ID
        """
        super().__init__(event_id, {
            'event_id': event_id,
            'community_id': community_id,
            'creator_id': creator_id,
            'event_type': event_type,
            'title': title,
            'target_user_id': target_user_id
        })


class EventClosedEvent(DomainEvent):
    """事件关闭领域事件"""

    def __init__(self, event_id: int, community_id: int, resolved_by: int,
                 closure_reason: str, closure_type: int):
        """
        初始化事件关闭事件

        Args:
            event_id: 事件ID
            community_id: 社区ID
            resolved_by: 解决者ID
            closure_reason: 关闭原因
            closure_type: 关闭类型（1=用户关闭，2=工作人员关闭）
        """
        super().__init__(event_id, {
            'event_id': event_id,
            'community_id': community_id,
            'resolved_by': resolved_by,
            'closure_reason': closure_reason,
            'closure_type': closure_type
        })


class EventCancelledEvent(DomainEvent):
    """事件取消领域事件"""

    def __init__(self, event_id: int, community_id: int, cancelled_by: int,
                 cancellation_reason: str):
        """
        初始化事件取消事件

        Args:
            event_id: 事件ID
            community_id: 社区ID
            cancelled_by: 取消者ID
            cancellation_reason: 取消原因
        """
        super().__init__(event_id, {
            'event_id': event_id,
            'community_id': community_id,
            'cancelled_by': cancelled_by,
            'cancellation_reason': cancellation_reason
        })


class EventSupportedEvent(DomainEvent):
    """事件应援领域事件"""

    def __init__(self, event_id: int, community_id: int, supporter_id: int,
                 message_content: str = None):
        """
        初始化事件应援事件

        Args:
            event_id: 事件ID
            community_id: 社区ID
            supporter_id: 应援者ID
            message_content: 应援消息内容
        """
        super().__init__(event_id, {
            'event_id': event_id,
            'community_id': community_id,
            'supporter_id': supporter_id,
            'message_content': message_content
        })


class EventLocationUpdatedEvent(DomainEvent):
    """事件位置更新领域事件"""

    def __init__(self, event_id: int, community_id: int, location: str,
                 location_lat: float = None, location_lon: float = None):
        """
        初始化事件位置更新事件

        Args:
            event_id: 事件ID
            community_id: 社区ID
            location: 位置描述
            location_lat: 纬度
            location_lon: 经度
        """
        super().__init__(event_id, {
            'event_id': event_id,
            'community_id': community_id,
            'location': location,
            'location_lat': location_lat,
            'location_lon': location_lon
        })


class EventMessageAddedEvent(DomainEvent):
    """事件消息添加领域事件"""

    def __init__(self, event_id: int, sender_id: int, message_type: str,
                 message_content: str = None, media_url: str = None,
                 message_tags: list = None):
        """
        初始化事件消息添加事件

        Args:
            event_id: 事件ID
            sender_id: 发送者ID
            message_type: 消息类型
            message_content: 消息内容
            media_url: 媒体URL
            message_tags: 消息标签
        """
        super().__init__(event_id, {
            'event_id': event_id,
            'sender_id': sender_id,
            'message_type': message_type,
            'message_content': message_content,
            'media_url': media_url,
            'message_tags': message_tags or []
        })


class EventStatusChangedEvent(DomainEvent):
    """事件状态变更领域事件"""

    def __init__(self, event_id: int, community_id: int, old_status: int,
                 new_status: int, operator_id: int):
        """
        初始化事件状态变更事件

        Args:
            event_id: 事件ID
            community_id: 社区ID
            old_status: 旧状态
            new_status: 新状态
            operator_id: 操作者ID
        """
        super().__init__(event_id, {
            'event_id': event_id,
            'community_id': community_id,
            'old_status': old_status,
            'new_status': new_status,
            'operator_id': operator_id
        })


class EventDetailsViewedEvent(DomainEvent):
    """事件详情查看领域事件"""

    def __init__(self, event_id: int, viewer_id: int, community_id: int):
        """
        初始化事件详情查看事件

        Args:
            event_id: 事件ID
            viewer_id: 查看者ID
            community_id: 社区ID
        """
        super().__init__(event_id, {
            'event_id': event_id,
            'viewer_id': viewer_id,
            'community_id': community_id
        })


class CommunityStatsRetrievedEvent(DomainEvent):
    """社区统计获取领域事件"""

    def __init__(self, community_id: int, active_events_count: int,
                 support_events_count: int):
        """
        初始化社区统计获取事件

        Args:
            community_id: 社区ID
            active_events_count: 活跃事件数量
            support_events_count: 支持事件数量
        """
        super().__init__(community_id, {
            'community_id': community_id,
            'active_events_count': active_events_count,
            'support_events_count': support_events_count
        })