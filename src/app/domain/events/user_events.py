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


class UserProfileUpdatedEvent(DomainEvent):
    """用户资料更新事件"""

    def __init__(self, user_id: int, updated_fields: dict):
        """
        初始化用户资料更新事件

        Args:
            user_id: 用户ID
            updated_fields: 更新的字段字典
        """
        super().__init__(user_id, {
            'user_id': user_id,
            'updated_fields': updated_fields
        })


class UserPasswordChangedEvent(DomainEvent):
    """用户密码修改事件"""

    def __init__(self, user_id: int):
        """
        初始化用户密码修改事件

        Args:
            user_id: 用户ID
        """
        super().__init__(user_id, {
            'user_id': user_id
        })


class UserAvatarUpdatedEvent(DomainEvent):
    """用户头像更新事件"""

    def __init__(self, user_id: int, avatar_url: str):
        """
        初始化用户头像更新事件

        Args:
            user_id: 用户ID
            avatar_url: 新头像URL
        """
        super().__init__(user_id, {
            'user_id': user_id,
            'avatar_url': avatar_url
        })


class UserStatusChangedEvent(DomainEvent):
    """用户状态变更事件"""

    def __init__(self, user_id: int, old_status: int, new_status: int):
        """
        初始化用户状态变更事件

        Args:
            user_id: 用户ID
            old_status: 旧状态
            new_status: 新状态
        """
        super().__init__(user_id, {
            'user_id': user_id,
            'old_status': old_status,
            'new_status': new_status
        })


class UserRoleChangedEvent(DomainEvent):
    """用户角色变更事件"""

    def __init__(self, user_id: int, old_role: int, new_role: int):
        """
        初始化用户角色变更事件

        Args:
            user_id: 用户ID
            old_role: 旧角色
            new_role: 新角色
        """
        super().__init__(user_id, {
            'user_id': user_id,
            'old_role': old_role,
            'new_role': new_role
        })