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


class CheckinCancelledEvent(DomainEvent):
    """打卡取消事件"""

    def __init__(self, record_id: int, user_id: int, rule_id: int, reason: str = None):
        """
        初始化打卡取消事件

        Args:
            record_id: 打卡记录ID
            user_id: 用户ID
            rule_id: 规则ID
            reason: 取消原因
        """
        super().__init__(record_id, {
            'record_id': record_id,
            'user_id': user_id,
            'rule_id': rule_id,
            'reason': reason
        })


class CheckinRuleCreatedEvent(DomainEvent):
    """打卡规则创建事件"""

    def __init__(self, rule_id: int, user_id: int, rule_name: str, frequency_type: int):
        """
        初始化打卡规则创建事件

        Args:
            rule_id: 规则ID
            user_id: 用户ID
            rule_name: 规则名称
            frequency_type: 频率类型
        """
        super().__init__(rule_id, {
            'rule_id': rule_id,
            'user_id': user_id,
            'rule_name': rule_name,
            'frequency_type': frequency_type
        })


class CheckinRuleUpdatedEvent(DomainEvent):
    """打卡规则更新事件"""

    def __init__(self, rule_id: int, user_id: int, updated_fields: dict):
        """
        初始化打卡规则更新事件

        Args:
            rule_id: 规则ID
            user_id: 用户ID
            updated_fields: 更新的字段
        """
        super().__init__(rule_id, {
            'rule_id': rule_id,
            'user_id': user_id,
            'updated_fields': updated_fields
        })


class CheckinRuleDeletedEvent(DomainEvent):
    """打卡规则删除事件"""

    def __init__(self, rule_id: int, user_id: int):
        """
        初始化打卡规则删除事件

        Args:
            rule_id: 规则ID
            user_id: 用户ID
        """
        super().__init__(rule_id, {
            'rule_id': rule_id,
            'user_id': user_id
        })


class CheckinRuleEnabledEvent(DomainEvent):
    """打卡规则启用事件"""

    def __init__(self, rule_id: int, user_id: int):
        """
        初始化打卡规则启用事件

        Args:
            rule_id: 规则ID
            user_id: 用户ID
        """
        super().__init__(rule_id, {
            'rule_id': rule_id,
            'user_id': user_id
        })


class CheckinRuleDisabledEvent(DomainEvent):
    """打卡规则禁用事件"""

    def __init__(self, rule_id: int, user_id: int):
        """
        初始化打卡规则禁用事件

        Args:
            rule_id: 规则ID
            user_id: 用户ID
        """
        super().__init__(rule_id, {
            'rule_id': rule_id,
            'user_id': user_id
        })