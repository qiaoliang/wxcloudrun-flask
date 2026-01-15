"""
社区相关领域事件
"""
from app.domain.events.domain_event import DomainEvent


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