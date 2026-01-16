"""
社区打卡规则仓储接口
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from database.flask_models import CommunityCheckinRule


class CommunityCheckinRuleRepository(ABC):
    """社区打卡规则仓储接口"""

    @abstractmethod
    def find_by_id(self, rule_id: int) -> Optional[CommunityCheckinRule]:
        """
        根据ID查找社区打卡规则

        Args:
            rule_id: 规则ID

        Returns:
            社区打卡规则对象，如果不存在则返回 None
        """
        pass

    @abstractmethod
    def find_by_community_id(self, community_id: int, include_deleted: bool = False) -> List[CommunityCheckinRule]:
        """
        根据社区ID查找所有打卡规则

        Args:
            community_id: 社区ID
            include_deleted: 是否包含已删除的规则

        Returns:
            社区打卡规则列表
        """
        pass

    @abstractmethod
    def find_by_community_id_and_status(self, community_id: int, status: int) -> List[CommunityCheckinRule]:
        """
        根据社区ID和状态查找打卡规则

        Args:
            community_id: 社区ID
            status: 规则状态（0=停用, 1=启用, 2=删除）

        Returns:
            社区打卡规则列表
        """
        pass

    @abstractmethod
    def find_by_created_by(self, created_by: int) -> List[CommunityCheckinRule]:
        """
        根据创建者ID查找打卡规则

        Args:
            created_by: 创建者ID

        Returns:
            社区打卡规则列表
        """
        pass

    @abstractmethod
    def save(self, rule: CommunityCheckinRule) -> CommunityCheckinRule:
        """
        保存社区打卡规则

        Args:
            rule: 社区打卡规则对象

        Returns:
            保存后的社区打卡规则对象
        """
        pass

    @abstractmethod
    def delete(self, rule_id: int) -> bool:
        """
        删除社区打卡规则（软删除）

        Args:
            rule_id: 规则ID

        Returns:
            是否删除成功
        """
        pass

    @abstractmethod
    def count_by_community_id(self, community_id: int, include_deleted: bool = False) -> int:
        """
        统计社区的打卡规则数量

        Args:
            community_id: 社区ID
            include_deleted: 是否包含已删除的规则

        Returns:
            规则数量
        """
        pass

    @abstractmethod
    def get_all_enabled_by_community_id(self, community_id: int) -> List[CommunityCheckinRule]:
        """
        获取社区所有启用的打卡规则

        Args:
            community_id: 社区ID

        Returns:
            启用的社区打卡规则列表
        """
        pass

    @abstractmethod
    def get_all_grouped_by_status(self, community_id: int) -> dict:
        """
        获取社区所有打卡规则，按状态分组

        Args:
            community_id: 社区ID

        Returns:
            按状态分组的规则字典 {'enabled': [], 'disabled': [], 'deleted': []}
        """
        pass

    @abstractmethod
    def find_active_rules(self) -> List[CommunityCheckinRule]:
        """查找所有启用的社区打卡规则"""
        pass

    @abstractmethod
    def find_all_day_rules(self) -> List[CommunityCheckinRule]:
        """查找所有启用的全天社区打卡规则"""
        pass

    @abstractmethod
    def find_all_day_rules(self) -> List[CommunityCheckinRule]:
        """查找所有启用的全天社区打卡规则"""
        pass