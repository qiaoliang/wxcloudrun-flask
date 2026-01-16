"""
社区聚合根

社区聚合是社区相关的核心业务概念，包含社区本身及其关联的打卡规则等。
"""
from typing import List, Optional

from app.domain.entities.community_entity import CommunityEntity
from app.domain.entities.community_checkin_rule_entity import CommunityCheckinRuleEntity


class CommunityAggregate:
    """
    社区聚合根

    聚合边界：
    - CommunityEntity（社区实体）
    - CommunityCheckinRuleEntity（社区的打卡规则）

    业务不变性：
    - 社区必须有至少一个主管
    - 社区成员数量不能超过限制（如果有）
    - 社区打卡规则的启用/禁用必须符合业务规则
    """

    def __init__(self, community_entity: CommunityEntity):
        """
        初始化社区聚合根

        Args:
            community_entity: 社区实体
        """
        self._community = community_entity
        self._checkin_rules: List[CommunityCheckinRuleEntity] = []

    @property
    def community(self) -> CommunityEntity:
        """获取社区实体"""
        return self._community

    @property
    def checkin_rules(self) -> List[CommunityCheckinRuleEntity]:
        """获取社区的打卡规则列表"""
        return self._checkin_rules

    def add_checkin_rule(self, rule: CommunityCheckinRuleEntity) -> None:
        """
        添加社区打卡规则

        Args:
            rule: 社区打卡规则实体
        """
        self._checkin_rules.append(rule)

    def remove_checkin_rule(self, rule_id: int) -> bool:
        """
        移除社区打卡规则

        Args:
            rule_id: 规则ID

        Returns:
            是否移除成功
        """
        for i, rule in enumerate(self._checkin_rules):
            if rule.community_rule_id == rule_id:
                self._checkin_rules.pop(i)
                return True
        return False

    def get_active_rules(self) -> List[CommunityCheckinRuleEntity]:
        """
        获取当前启用的打卡规则

        Returns:
            启用的打卡规则列表
        """
        return [rule for rule in self._checkin_rules if rule.is_enabled()]

    def __eq__(self, other) -> bool:
        if not isinstance(other, CommunityAggregate):
            return False
        return self._community == other._community

    def __hash__(self) -> int:
        return hash(self._community)