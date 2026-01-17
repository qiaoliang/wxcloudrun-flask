"""
社区仓储接口

定义社区相关的数据访问操作。
"""
from abc import abstractmethod
from typing import List, Optional

from .base import BaseRepository
from database.flask_models import Community


class CommunityRepository(BaseRepository[Community]):
    """社区仓储接口"""

    @abstractmethod
    def find_by_name(self, name: str) -> Optional[Community]:
        """
        根据社区名称查找社区

        Args:
            name: 社区名称

        Returns:
            Optional[Community]: 社区对象，如果不存在则返回 None
        """
        pass

    @abstractmethod
    def find_by_creator_id(self, creator_id: int) -> List[Community]:
        """
        根据创建者ID查找社区列表

        Args:
            creator_id: 创建者ID

        Returns:
            List[Community]: 社区列表
        """
        pass

    @abstractmethod
    def find_by_manager_id(self, manager_id: int) -> List[Community]:
        """
        根据主管ID查找社区列表

        Args:
            manager_id: 主管ID

        Returns:
            List[Community]: 社区列表
        """
        pass

    @abstractmethod
    def find_default_community(self) -> Optional[Community]:
        """
        查找默认社区

        Returns:
            Optional[Community]: 默认社区对象，如果不存在则返回 None
        """
        pass

    @abstractmethod
    def find_active_communities(self) -> List[Community]:
        """
        查找所有活跃的社区

        Returns:
            List[Community]: 活跃社区列表
        """
        pass

    @abstractmethod
    def exists_by_name(self, name: str) -> bool:
        """
        检查社区名称是否存在

        Args:
            name: 社区名称

        Returns:
            bool: 如果存在返回 True，否则返回 False
        """
        pass

    @abstractmethod
    def search(
        self,
        keyword: Optional[str] = None,
        province: Optional[str] = None,
        city: Optional[str] = None,
        district: Optional[str] = None,
        status: Optional[int] = None
    ) -> List[Community]:
        """
        搜索社区

        Args:
            keyword: 搜索关键词（社区名称、描述）
            province: 省份
            city: 城市
            district: 区县
            status: 社区状态

        Returns:
            List[Community]: 社区列表
        """
        pass

    @abstractmethod
    def find_by_id(self, community_id: int) -> Optional[Community]:
        """
        根据ID查找社区

        Args:
            community_id: 社区ID

        Returns:
            Optional[Community]: 社区对象，如果不存在则返回 None
        """
        pass