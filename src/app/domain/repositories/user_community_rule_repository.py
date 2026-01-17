"""
用户社区规则映射仓储接口
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from database.flask_models import UserCommunityRule


class UserCommunityRuleRepository(ABC):
    """用户社区规则映射仓储接口"""

    @abstractmethod
    def find_by_id(self, mapping_id: int) -> Optional[UserCommunityRule]:
        """
        根据ID查找映射

        Args:
            mapping_id: 映射ID

        Returns:
            用户社区规则映射对象，如果不存在则返回 None
        """
        pass

    @abstractmethod
    def find_by_user_id(self, user_id: int, include_inactive: bool = False) -> List[UserCommunityRule]:
        """
        根据用户ID查找所有映射

        Args:
            user_id: 用户ID
            include_inactive: 是否包含未激活的映射

        Returns:
            用户社区规则映射列表
        """
        pass

    @abstractmethod
    def find_by_community_rule_id(self, community_rule_id: int, include_inactive: bool = False) -> List[UserCommunityRule]:
        """
        根据社区规则ID查找所有映射

        Args:
            community_rule_id: 社区规则ID
            include_inactive: 是否包含未激活的映射

        Returns:
            用户社区规则映射列表
        """
        pass

    @abstractmethod
    def find_by_user_and_rule(self, user_id: int, community_rule_id: int) -> Optional[UserCommunityRule]:
        """
        根据用户ID和社区规则ID查找映射

        Args:
            user_id: 用户ID
            community_rule_id: 社区规则ID

        Returns:
            用户社区规则映射对象，如果不存在则返回 None
        """
        pass

    @abstractmethod
    def save(self, mapping: UserCommunityRule) -> UserCommunityRule:
        """
        保存用户社区规则映射

        Args:
            mapping: 用户社区规则映射对象

        Returns:
            保存后的用户社区规则映射对象
        """
        pass

    @abstractmethod
    def delete(self, mapping_id: int) -> bool:
        """
        删除用户社区规则映射

        Args:
            mapping_id: 映射ID

        Returns:
            是否删除成功
        """
        pass

    @abstractmethod
    def activate(self, mapping_id: int) -> bool:
        """
        激活用户社区规则映射

        Args:
            mapping_id: 映射ID

        Returns:
            是否激活成功
        """
        pass

    @abstractmethod
    def deactivate(self, mapping_id: int) -> bool:
        """
        停用用户社区规则映射

        Args:
            mapping_id: 映射ID

        Returns:
            是否停用成功
        """
        pass

    @abstractmethod
    def count_by_user_id(self, user_id: int, include_inactive: bool = False) -> int:
        """
        统计用户的社区规则映射数量

        Args:
            user_id: 用户ID
            include_inactive: 是否包含未激活的映射

        Returns:
            映射数量
        """
        pass

    @abstractmethod
    def count_by_community_rule_id(self, community_rule_id: int, include_inactive: bool = False) -> int:
        """
        统计社区规则的映射数量

        Args:
            community_rule_id: 社区规则ID
            include_inactive: 是否包含未激活的映射

        Returns:
            映射数量
        """
        pass

    @abstractmethod
    def deactivate_by_user_and_community(
        self,
        user_id: int,
        community_id: int
    ) -> int:
        """
        停用用户在指定社区的所有规则映射

        Args:
            user_id: 用户ID
            community_id: 社区ID

        Returns:
            int: 停用的规则数量
        """
        pass