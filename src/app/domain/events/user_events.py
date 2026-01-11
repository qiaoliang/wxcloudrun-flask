"""
用户相关领域事件
"""
from app.domain.events.domain_event import DomainEvent


class UserCreatedEvent(DomainEvent):
    """用户创建事件"""

    def __init__(self, user_id: int, phone_number: str):
        """
        初始化用户创建事件

        Args:
            user_id: 用户ID
            phone_number: 手机号
        """
        super().__init__(user_id, {
            'user_id': user_id,
            'phone_number': phone_number
        })


class UserJoinedCommunityEvent(DomainEvent):
    """用户加入社区事件"""

    def __init__(self, user_id: int, community_id: int):
        """
        初始化用户加入社区事件

        Args:
            user_id: 用户ID
            community_id: 社区ID
        """
        super().__init__(user_id, {
            'user_id': user_id,
            'community_id': community_id
        })


class UserLeftCommunityEvent(DomainEvent):
    """用户离开社区事件"""

    def __init__(self, user_id: int, community_id: int):
        """
        初始化用户离开社区事件

        Args:
            user_id: 用户ID
            community_id: 社区ID
        """
        super().__init__(user_id, {
            'user_id': user_id,
            'community_id': community_id
        })