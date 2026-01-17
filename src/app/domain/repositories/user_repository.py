"""
用户仓储接口

定义用户相关的数据访问操作。
"""
from abc import abstractmethod
from typing import List, Optional

from .base import BaseRepository
from database.flask_models import User


class UserRepository(BaseRepository[User]):
    """用户仓储接口"""

    @abstractmethod
    def find_by_openid(self, openid: str) -> Optional[User]:
        """
        根据微信openid查找用户

        Args:
            openid: 微信openid

        Returns:
            Optional[User]: 用户对象，如果不存在则返回 None
        """
        pass

    @abstractmethod
    def find_by_phone_hash(self, phone_hash: str) -> Optional[User]:
        """
        根据手机号哈希查找用户

        Args:
            phone_hash: 手机号哈希

        Returns:
            Optional[User]: 用户对象，如果不存在则返回 None
        """
        pass

    @abstractmethod
    def find_by_refresh_token(self, refresh_token: str) -> Optional[User]:
        """
        根据refresh token查找用户

        Args:
            refresh_token: 刷新令牌

        Returns:
            Optional[User]: 用户对象，如果不存在则返回 None
        """
        pass

    @abstractmethod
    def find_by_community_id(self, community_id: int) -> List[User]:
        """
        根据社区ID查找用户列表

        Args:
            community_id: 社区ID

        Returns:
            List[User]: 用户列表
        """
        pass

    @abstractmethod
    def find_by_role(self, role: int) -> List[User]:
        """
        根据角色查找用户列表

        Args:
            role: 角色ID

        Returns:
            List[User]: 用户列表
        """
        pass

    @abstractmethod
    def search_users(self, keyword: str, community_id: Optional[int] = None) -> List[User]:
        """
        搜索用户

        Args:
            keyword: 搜索关键词（昵称、手机号、姓名）
            community_id: 社区ID（可选）

        Returns:
            List[User]: 用户列表
        """
        pass

    @abstractmethod
    def search_users_paginated(self, keyword: str, page: int, per_page: int, search_type: str = 'all', exclude_blackroom: bool = False) -> tuple[List[dict], int]:
        """
        分页搜索用户

        Args:
            keyword: 搜索关键词
            page: 页码
            per_page: 每页数量
            search_type: 搜索类型 (all, phone, nickname)
            exclude_blackroom: 是否排除黑名单房间

        Returns:
            tuple[List[dict], int]: (用户数据列表, 总数)
        """
        pass

    @abstractmethod
    def exists_by_openid(self, openid: str) -> bool:
        """
        检查微信openid是否存在

        Args:
            openid: 微信openid

        Returns:
            bool: 如果存在返回 True，否则返回 False
        """
        pass

    @abstractmethod
    def exists_by_phone_hash(self, phone_hash: str) -> bool:
        """
        检查手机号哈希是否存在

        Args:
            phone_hash: 手机号哈希

        Returns:
            bool: 如果存在返回 True，否则返回 False
        """
        pass

    @abstractmethod
    def find_by_id(self, user_id: int) -> Optional[User]:
        """
        根据用户ID查找用户

        Args:
            user_id: 用户ID

        Returns:
            Optional[User]: 用户对象，如果不存在则返回 None
        """
        pass