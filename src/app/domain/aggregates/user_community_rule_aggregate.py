"""
用户社区规则聚合根

用户社区规则聚合是用户和社区之间规则关联的核心业务概念。
"""
from typing import Optional

from app.domain.entities.user_community_rule_entity import UserCommunityRuleEntity


class UserCommunityRuleAggregate:
    """
    用户社区规则聚合根

    聚合边界：
    - UserCommunityRuleEntity（用户社区规则关联实体）

    业务不变性：
    - 用户社区规则关联必须属于一个用户和一个社区规则
    - 用户社区规则的状态必须符合业务规则
    - 用户社区规则的激活/禁用必须符合权限要求
    """

    def __init__(self, user_community_rule: UserCommunityRuleEntity):
        """
        初始化用户社区规则聚合根

        Args:
            user_community_rule: 用户社区规则关联实体
        """
        self._user_community_rule = user_community_rule

    @property
    def user_community_rule(self) -> UserCommunityRuleEntity:
        """获取用户社区规则关联实体"""
        return self._user_community_rule

    def activate(self) -> None:
        """
        激活规则

        Raises:
            ValueError: 如果规则已经激活
        """
        if self._user_community_rule.is_active():
            raise ValueError("规则已经激活")

        self._user_community_rule.activate()

    def deactivate(self) -> None:
        """
        禁用规则

        Raises:
            ValueError: 如果规则已经禁用
        """
        if not self._user_community_rule.is_active():
            raise ValueError("规则已经禁用")

        self._user_community_rule.deactivate()

    def is_active(self) -> bool:
        """
        检查规则是否激活

        Returns:
            是否激活
        """
        return self._user_community_rule.is_active()

    def can_be_activated_by(self, user_id: int, is_staff: bool) -> bool:
        """
        检查规则是否可以被指定用户激活

        Args:
            user_id: 用户ID
            is_staff: 是否是社区工作人员

        Returns:
            是否可以被激活
        """
        # 规则已经激活
        if self.is_active():
            return False

        # 只有规则所属用户或社区工作人员可以激活
        return user_id == self._user_community_rule.user_id or is_staff

    def can_be_deactivated_by(self, user_id: int, is_staff: bool) -> bool:
        """
        检查规则是否可以被指定用户禁用

        Args:
            user_id: 用户ID
            is_staff: 是否是社区工作人员

        Returns:
            是否可以被禁用
        """
        # 规则已经禁用
        if not self.is_active():
            return False

        # 只有规则所属用户或社区工作人员可以禁用
        return user_id == self._user_community_rule.user_id or is_staff

    def get_rule_info(self) -> dict:
        """
        获取规则信息

        Returns:
            规则信息字典
        """
        return {
            'user_rule_id': self._user_community_rule.user_rule_id,
            'user_id': self._user_community_rule.user_id,
            'community_rule_id': self._user_community_rule.community_rule_id,
            'rule_name': self._user_community_rule.rule_name,
            'rule_type': self._user_community_rule.rule_type,
            'checkin_time': self._user_community_rule.checkin_time,
            'checkin_frequency': self._user_community_rule.checkin_frequency,
            'is_active': self._user_community_rule.is_active(),
            'created_at': self._user_community_rule.created_at.isoformat() if self._user_community_rule.created_at else None,
            'updated_at': self._user_community_rule.updated_at.isoformat() if self._user_community_rule.updated_at else None
        }

    def __eq__(self, other) -> bool:
        if not isinstance(other, UserCommunityRuleAggregate):
            return False
        return self._user_community_rule == other._user_community_rule

    def __hash__(self) -> int:
        return hash(self._user_community_rule)