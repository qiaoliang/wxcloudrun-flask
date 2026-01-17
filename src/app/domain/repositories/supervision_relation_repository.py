"""
监督关系仓储接口
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from database.flask_models import SupervisionRuleRelation


class SupervisionRelationRepository(ABC):
    """监督关系仓储接口"""

    @abstractmethod
    def find_by_id(self, relation_id: int) -> Optional[SupervisionRuleRelation]:
        """
        根据ID查找监督关系

        Args:
            relation_id: 监督关系ID

        Returns:
            Optional[SupervisionRuleRelation]: 监督关系对象，不存在时返回None
        """
        pass

    @abstractmethod
    def find_by_supervisor_id(self, supervisor_id: int) -> List[SupervisionRuleRelation]:
        """
        根据监督者ID查找监督关系列表

        Args:
            supervisor_id: 监督者用户ID

        Returns:
            List[SupervisionRuleRelation]: 监督关系列表
        """
        pass

    @abstractmethod
    def find_by_solo_user_id(self, solo_user_id: int) -> List[SupervisionRuleRelation]:
        """
        根据被监督者ID查找监督关系列表

        Args:
            solo_user_id: 被监督者用户ID

        Returns:
            List[SupervisionRuleRelation]: 监督关系列表
        """
        pass

    @abstractmethod
    def find_by_users_and_rule(self, supervisor_id: int, solo_user_id: int, rule_id: int) -> Optional[SupervisionRuleRelation]:
        """
        根据监督者、被监督者和规则ID查找监督关系

        Args:
            supervisor_id: 监督者用户ID
            solo_user_id: 被监督者用户ID
            rule_id: 规则ID

        Returns:
            Optional[SupervisionRuleRelation]: 监督关系对象，不存在时返回None
        """
        pass

    @abstractmethod
    def save(self, entity: SupervisionRuleRelation) -> SupervisionRuleRelation:
        """
        保存监督关系

        Args:
            entity: 监督关系对象

        Returns:
            SupervisionRuleRelation: 保存后的监督关系对象
        """
        pass

    @abstractmethod
    def update(self, entity: SupervisionRuleRelation) -> SupervisionRuleRelation:
        """
        更新监督关系

        Args:
            entity: 监督关系对象

        Returns:
            SupervisionRuleRelation: 更新后的监督关系对象
        """
        pass

    @abstractmethod
    def delete(self, relation_id: int) -> bool:
        """
        删除监督关系

        Args:
            relation_id: 监督关系ID

        Returns:
            bool: 删除是否成功
        """
        pass

    @abstractmethod
    def find_expired_invitations(self) -> List[SupervisionRuleRelation]:
        """
        查找所有已过期的邀请

        Returns:
            List[SupervisionRuleRelation]: 已过期的邀请列表
        """
        pass

    @abstractmethod
    def batch_update_status(self, relation_ids: List[int], new_status: int) -> int:
        """
        批量更新监督关系状态

        Args:
            relation_ids: 监督关系ID列表
            new_status: 新状态值

        Returns:
            int: 更新的记录数
        """
        pass

    @abstractmethod
    def find_by_invite_token(self, invite_token: str, status: Optional[int] = None) -> List[SupervisionRuleRelation]:
        """
        根据邀请令牌查找监督关系

        Args:
            invite_token: 邀请令牌
            status: 可选的状态过滤

        Returns:
            List[SupervisionRuleRelation]: 监督关系列表
        """
        pass

    @abstractmethod
    def update_status(self, relation_id: int, new_status: int) -> bool:
        """
        更新监督关系状态

        Args:
            relation_id: 监督关系ID
            new_status: 新状态值

        Returns:
            bool: 更新是否成功
        """
        pass

    @abstractmethod
    def delete_entity(self, relation: SupervisionRuleRelation) -> bool:
        """
        删除监督关系实体

        Args:
            relation: 监督关系对象

        Returns:
            bool: 删除是否成功
        """
        pass
