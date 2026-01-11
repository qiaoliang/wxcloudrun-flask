"""
社区领域实体

封装社区相关的业务逻辑。
"""
from typing import Optional, List
from datetime import datetime

from database.flask_models import Community, User


class CommunityEntity:
    """社区领域实体"""

    def __init__(self, community: Community):
        """
        初始化社区领域实体

        Args:
            community: SQLAlchemy Community 模型实例
        """
        self._community = community

    @property
    def community(self) -> Community:
        """获取底层的 SQLAlchemy Community 模型"""
        return self._community

    @property
    def community_id(self) -> int:
        """获取社区ID"""
        return self._community.community_id

    @property
    def name(self) -> str:
        """获取社区名称"""
        return self._community.community_name

    @property
    def creator_id(self) -> int:
        """获取创建者ID"""
        return self._community.creator_id

    @property
    def is_active(self) -> bool:
        """社区是否活跃"""
        return self._community.status == 1

    @property
    def member_count(self) -> int:
        """获取成员数量"""
        return len([u for u in self._community.users if u.status == 1])

    def has_member(self, user_id: int) -> bool:
        """
        检查用户是否在社区中

        Args:
            user_id: 用户ID

        Returns:
            bool: 用户是否在社区中
        """
        return any(u.user_id == user_id and u.status == 1 for u in self._community.users)

    def add_member(self, user: User) -> None:
        """
        添加成员到社区

        Args:
            user: 用户实例
        """
        user.community_id = self._community.community_id
        user.community_joined_at = datetime.now()

    def remove_member(self, user: User) -> None:
        """
        从社区移除成员

        Args:
            user: 用户实例
        """
        user.community_id = None
        user.community_joined_at = None

    def update_info(self, name: Optional[str] = None, description: Optional[str] = None,
                    address: Optional[str] = None) -> None:
        """
        更新社区信息

        Args:
            name: 社区名称
            description: 社区描述
            address: 社区地址
        """
        if name is not None:
            if len(name.strip()) > 0:
                self._community.community_name = name.strip()[:100]

        if description is not None:
            self._community.description = description[:500] if description else None

        if address is not None:
            self._community.address = address[:200] if address else None

    def activate(self) -> None:
        """激活社区"""
        self._community.status = 1

    def deactivate(self) -> None:
        """停用社区"""
        self._community.status = 0

    def is_special_community(self) -> bool:
        """
        是否为特殊社区（黑名单、测试等）

        Returns:
            bool: 是否为特殊社区
        """
        return self._community.community_id in [1, 2]

    def __eq__(self, other) -> bool:
        if not isinstance(other, CommunityEntity):
            return False
        return self._community.community_id == other._community.community_id

    def __hash__(self) -> int:
        return hash(self._community.community_id)