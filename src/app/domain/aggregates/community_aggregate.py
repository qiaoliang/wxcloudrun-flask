"""
社区聚合根

社区聚合是社区相关的核心业务概念，包含社区本身及其关联的成员、打卡规则、事件等。
"""
from typing import List, Optional

from app.domain.entities.community_entity import CommunityEntity
from app.domain.entities.community_checkin_rule_entity import CommunityCheckinRuleEntity
from app.domain.entities.community_event_entity import CommunityEventEntity


class CommunityAggregate:
    """
    社区聚合根

    聚合边界：
    - CommunityEntity（社区实体）
    - CommunityCheckinRuleEntity（社区的打卡规则）
    - CommunityEventEntity（社区的事件）

    业务不变性：
    - 社区必须有至少一个主管
    - 社区成员数量不能超过限制（如果有）
    - 社区打卡规则的启用/禁用必须符合业务规则
    - 社区事件的处理必须符合权限要求
    """

    def __init__(self, community_entity: CommunityEntity):
        """
        初始化社区聚合根

        Args:
            community_entity: 社区实体
        """
        self._community = community_entity
        self._checkin_rules: List[CommunityCheckinRuleEntity] = []
        self._events: List[CommunityEventEntity] = []

    @property
    def community(self) -> CommunityEntity:
        """获取社区实体"""
        return self._community

    @property
    def checkin_rules(self) -> List[CommunityCheckinRuleEntity]:
        """获取社区的打卡规则列表"""
        return self._checkin_rules

    @property
    def events(self) -> List[CommunityEventEntity]:
        """获取社区的事件列表"""
        return self._events

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

    def add_event(self, event: CommunityEventEntity) -> None:
        """
        添加社区事件

        Args:
            event: 社区事件实体
        """
        self._events.append(event)

    def get_pending_events(self) -> List[CommunityEventEntity]:
        """
        获取待处理的事件

        Returns:
            待处理的事件列表
        """
        return [event for event in self._events if event.is_pending()]

    def get_resolved_events(self) -> List[CommunityEventEntity]:
        """
        获取已解决的事件

        Returns:
            已解决的事件列表
        """
        return [event for event in self._events if event.is_resolved()]

    def get_cancelled_events(self) -> List[CommunityEventEntity]:
        """
        获取已取消的事件

        Returns:
            已取消的事件列表
        """
        return [event for event in self._events if event.is_cancelled()]

    def resolve_event(self, event_id: int, reason: str) -> bool:
        """
        解决事件

        Args:
            event_id: 事件ID
            reason: 解决原因

        Returns:
            是否解决成功
        """
        for event in self._events:
            if event.event_id == event_id:
                event.resolve(reason)
                return True
        return False

    def cancel_event(self, event_id: int, reason: str) -> bool:
        """
        取消事件

        Args:
            event_id: 事件ID
            reason: 取消原因

        Returns:
            是否取消成功
        """
        for event in self._events:
            if event.event_id == event_id:
                event.cancel(reason)
                return True
        return False

    def __eq__(self, other) -> bool:
        if not isinstance(other, CommunityAggregate):
            return False
        return self._community == other._community

    def __hash__(self) -> int:
        return hash(self._community)