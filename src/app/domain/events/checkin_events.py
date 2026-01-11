"""
打卡相关领域事件
"""
from app.domain.events.domain_event import DomainEvent


class CheckinCompletedEvent(DomainEvent):
    """打卡完成事件"""

    def __init__(self, record_id: int, user_id: int, rule_id: int, checkin_time):
        """
        初始化打卡完成事件

        Args:
            record_id: 打卡记录ID
            user_id: 用户ID
            rule_id: 规则ID
            checkin_time: 打卡时间
        """
        super().__init__(record_id, {
            'record_id': record_id,
            'user_id': user_id,
            'rule_id': rule_id,
            'checkin_time': checkin_time
        })


class CheckinMissedEvent(DomainEvent):
    """打卡错过事件"""

    def __init__(self, record_id: int, user_id: int, rule_id: int, scheduled_time):
        """
        初始化打卡错过事件

        Args:
            record_id: 打卡记录ID
            user_id: 用户ID
            rule_id: 规则ID
            scheduled_time: 计划打卡时间
        """
        super().__init__(record_id, {
            'record_id': record_id,
            'user_id': user_id,
            'rule_id': rule_id,
            'scheduled_time': scheduled_time
        })