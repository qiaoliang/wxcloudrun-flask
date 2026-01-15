"""
打卡规则聚合根

打卡规则聚合是打卡规则相关的核心业务概念，包含规则本身及其关联的打卡记录。
"""
from typing import List, Optional
from datetime import datetime

from app.domain.entities.checkin_rule_entity import CheckinRuleEntity
from app.domain.entities.checkin_record_entity import CheckinRecordEntity
from app.domain.events.checkin_events import (
    CheckinCompletedEvent,
    CheckinMissedEvent,
    CheckinCancelledEvent,
    CheckinRuleEnabledEvent,
    CheckinRuleDisabledEvent
)
from app.domain.events.event_bus import EventBus


class CheckinRuleAggregate:
    """
    打卡规则聚合根

    聚合边界：
    - CheckinRuleEntity（打卡规则实体）
    - CheckinRecordEntity（打卡记录）

    业务不变性：
    - 规则必须关联到一个有效的用户
    - 规则的启用/禁用必须符合业务规则
    - 打卡记录必须符合规则的时间要求
    """

    def __init__(self, rule_entity: CheckinRuleEntity):
        """
        初始化打卡规则聚合根

        Args:
            rule_entity: 打卡规则实体
        """
        self._rule = rule_entity
        self._records: List[CheckinRecordEntity] = []
        self._events: List = []

    @property
    def rule(self) -> CheckinRuleEntity:
        """获取打卡规则实体"""
        return self._rule

    @property
    def records(self) -> List[CheckinRecordEntity]:
        """获取打卡记录列表"""
        return self._records

    @property
    def events(self) -> List:
        """获取待发布的领域事件"""
        return self._events

    def add_record(self, record: CheckinRecordEntity) -> None:
        """
        添加打卡记录

        Args:
            record: 打卡记录实体
        """
        self._records.append(record)

    def complete_checkin(self, record_id: int, checkin_time: datetime) -> None:
        """
        完成打卡

        Args:
            record_id: 打卡记录ID
            checkin_time: 打卡时间
        """
        event = CheckinCompletedEvent(
            record_id=record_id,
            user_id=self._rule.user_id,
            rule_id=self._rule.rule_id,
            checkin_time=checkin_time
        )
        self._events.append(event)
        EventBus.publish(event)

    def miss_checkin(self, record_id: int, scheduled_time: datetime) -> None:
        """
        错过打卡

        Args:
            record_id: 打卡记录ID
            scheduled_time: 计划打卡时间
        """
        event = CheckinMissedEvent(
            record_id=record_id,
            user_id=self._rule.user_id,
            rule_id=self._rule.rule_id,
            scheduled_time=scheduled_time
        )
        self._events.append(event)
        EventBus.publish(event)

    def cancel_checkin(self, record_id: int, reason: str = None) -> None:
        """
        取消打卡

        Args:
            record_id: 打卡记录ID
            reason: 取消原因
        """
        event = CheckinCancelledEvent(
            record_id=record_id,
            user_id=self._rule.user_id,
            rule_id=self._rule.rule_id,
            reason=reason
        )
        self._events.append(event)
        EventBus.publish(event)

    def enable(self) -> None:
        """启用规则"""
        self._rule.enable()
        event = CheckinRuleEnabledEvent(
            rule_id=self._rule.rule_id,
            user_id=self._rule.user_id
        )
        self._events.append(event)
        EventBus.publish(event)

    def disable(self) -> None:
        """禁用规则"""
        self._rule.disable()
        event = CheckinRuleDisabledEvent(
            rule_id=self._rule.rule_id,
            user_id=self._rule.user_id
        )
        self._events.append(event)
        EventBus.publish(event)

    def soft_delete(self) -> None:
        """软删除规则"""
        self._rule.soft_delete()

    def clear_events(self) -> None:
        """清除已发布的事件"""
        self._events.clear()

    def get_records_by_date(self, date: datetime) -> List[CheckinRecordEntity]:
        """
        获取指定日期的打卡记录

        Args:
            date: 日期

        Returns:
            打卡记录列表
        """
        return [
            record for record in self._records
            if record.checkin_date.date() == date.date()
        ]

    def get_today_record(self, date: datetime) -> Optional[CheckinRecordEntity]:
        """
        获取今天的打卡记录

        Args:
            date: 日期

        Returns:
            打卡记录，如果不存在则返回 None
        """
        records = self.get_records_by_date(date)
        return records[0] if records else None

    def get_missed_records(self, days: int = 7) -> List[CheckinRecordEntity]:
        """
        获取最近N天错过的打卡记录

        Args:
            days: 天数

        Returns:
            错过的打卡记录列表
        """
        cutoff_date = datetime.now() - datetime.timedelta(days=days)
        return [
            record for record in self._records
            if record.is_missed() and record.checkin_date >= cutoff_date
        ]

    def calculate_completion_rate(self, days: int = 7) -> float:
        """
        计算最近N天的完成率

        Args:
            days: 天数

        Returns:
            完成率（0-1之间的浮点数）
        """
        cutoff_date = datetime.now() - datetime.timedelta(days=days)
        recent_records = [
            record for record in self._records
            if record.checkin_date >= cutoff_date
        ]

        if not recent_records:
            return 0.0

        completed = sum(1 for record in recent_records if record.is_completed())
        return completed / len(recent_records)

    def __eq__(self, other) -> bool:
        if not isinstance(other, CheckinRuleAggregate):
            return False
        return self._rule == other._rule

    def __hash__(self) -> int:
        return hash(self._rule)