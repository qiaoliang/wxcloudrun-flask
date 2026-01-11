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