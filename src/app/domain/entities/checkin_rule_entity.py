"""
打卡规则领域实体

封装打卡规则相关的业务逻辑。
"""
from typing import Optional
from datetime import datetime, time

from database.flask_models import CheckinRule


class CheckinRuleEntity:
    """打卡规则领域实体"""

    def __init__(self, rule: CheckinRule):
        """
        初始化打卡规则领域实体

        Args:
            rule: SQLAlchemy CheckinRule 模型实例
        """
        self._rule = rule

    @property
    def rule(self) -> CheckinRule:
        """获取底层的 SQLAlchemy CheckinRule 模型"""
        return self._rule

    @property
    def rule_id(self) -> int:
        """获取规则ID"""
        return self._rule.rule_id

    @property
    def user_id(self) -> int:
        """获取用户ID"""
        return self._rule.user_id

    @property
    def name(self) -> str:
        """获取规则名称"""
        return self._rule.rule_name

    @property
    def is_enabled(self) -> bool:
        """规则是否启用"""
        return self._rule.is_enabled == 1

    @property
    def is_deleted(self) -> bool:
        """规则是否已删除"""
        return self._rule.is_deleted == 1

    @property
    def frequency_type(self) -> int:
        """获取频率类型"""
        return self._rule.frequency_type

    @property
    def time_slot_type(self) -> int:
        """获取时间段类型"""
        return self._rule.time_slot_type

    @property
    def custom_time(self) -> Optional[str]:
        """获取自定义时间"""
        return self._rule.custom_time

    def enable(self) -> None:
        """启用规则"""
        self._rule.is_enabled = 1
        self._rule.updated_at = datetime.now()

    def disable(self) -> None:
        """禁用规则"""
        self._rule.is_enabled = 0
        self._rule.updated_at = datetime.now()

    def soft_delete(self) -> None:
        """软删除规则"""
        self._rule.is_deleted = 1
        self._rule.updated_at = datetime.now()

    def update(self, name: Optional[str] = None, frequency_type: Optional[int] = None,
               time_slot_type: Optional[int] = None, custom_time: Optional[str] = None,
               icon_url: Optional[str] = None) -> None:
        """
        更新规则

        Args:
            name: 规则名称
            frequency_type: 频率类型
            time_slot_type: 时间段类型
            custom_time: 自定义时间
            icon_url: 图标URL
        """
        if name is not None:
            if len(name.strip()) > 0:
                self._rule.rule_name = name.strip()[:100]

        if frequency_type is not None:
            if frequency_type in [0, 1, 2]:
                self._rule.frequency_type = frequency_type

        if time_slot_type is not None:
            if time_slot_type in [0, 1, 2, 3, 4]:
                self._rule.time_slot_type = time_slot_type

        if custom_time is not None:
            # 验证时间格式 HH:MM:SS
            try:
                time.fromisoformat(custom_time)
                self._rule.custom_time = custom_time
            except ValueError:
                pass

        if icon_url is not None:
            if icon_url.startswith(('http://', 'https://')) and len(icon_url) <= 500:
                self._rule.icon_url = icon_url.strip()

        self._rule.updated_at = datetime.now()

    def calculate_planned_checkin_time(self, reference_date: datetime = None) -> Optional[datetime]:
        """
        计算计划的打卡时间

        Args:
            reference_date: 参考日期（默认为今天）

        Returns:
            计划打卡时间，如果无法计算则返回 None
        """
        if reference_date is None:
            reference_date = datetime.now()

        if not self.is_enabled or self.is_deleted:
            return None

        # 自定义时间
        if self.time_slot_type == 4 and self.custom_time:
            try:
                time_obj = time.fromisoformat(self.custom_time)
                return datetime.combine(reference_date.date(), time_obj)
            except ValueError:
                return None

        # 其他时间段类型
        time_mapping = {
            0: time(8, 0),   # 早晨
            1: time(12, 0),  # 中午
            2: time(18, 0),  # 傍晚
            3: time(21, 0)   # 晚上
        }

        time_obj = time_mapping.get(self.time_slot_type)
        if time_obj:
            return datetime.combine(reference_date.date(), time_obj)

        return None

    def __eq__(self, other) -> bool:
        if not isinstance(other, CheckinRuleEntity):
            return False
        return self._rule.rule_id == other._rule.rule_id

    def __hash__(self) -> int:
        return hash(self._rule.rule_id)