"""
打卡规则领域实体

纯领域实体,不依赖 ORM 模型,遵循 DDD 原则
"""
from typing import Optional
from datetime import datetime, time
from dataclasses import dataclass, field


@dataclass
class CheckinRuleEntity:
    """
    打卡规则领域实体

    这是一个纯领域实体,不依赖任何 ORM 框架。
    所有属性都通过数据类定义,确保不可变性和值对象语义。
    """
    # 基础属性
    rule_id: int
    user_id: int
    rule_name: str
    frequency_type: int  # 0:每天, 1:每周, 2:自定义
    time_slot_type: int  # 0:早晨, 1:中午, 2:傍晚, 3:晚上, 4:自定义
    status: int  # 0:禁用, 1:启用, 2:删除

    # 可选属性
    community_id: Optional[int] = None
    icon_url: Optional[str] = None
    custom_time: Optional[str] = None  # HH:MM:SS 格式
    week_days: Optional[int] = None  # 位掩码整数: 1=周一, 2=周二, ..., 64=周日
    custom_start_date: Optional[datetime] = None
    custom_end_date: Optional[datetime] = None

    # 时间戳
    created_at: Optional[datetime] = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = field(default_factory=datetime.now)

    # 领域事件(由聚合根管理)
    _events: list = field(default_factory=list, init=False, repr=False)

    @classmethod
    def create(cls, rule_id: int, user_id: int, rule_name: str,
              frequency_type: int, time_slot_type: int, status: int = 1,
              **kwargs) -> 'CheckinRuleEntity':
        """
        工厂方法:创建打卡规则实体

        Args:
            rule_id: 规则ID
            user_id: 用户ID
            rule_name: 规则名称
            frequency_type: 频率类型
            time_slot_type: 时间段类型
            status: 状态(默认启用)
            **kwargs: 其他可选属性

        Returns:
            CheckinRuleEntity: 打卡规则实体
        """
        return cls(
            rule_id=rule_id,
            user_id=user_id,
            rule_name=rule_name[:100],  # 限制长度
            frequency_type=frequency_type,
            time_slot_type=time_slot_type,
            status=status,
            community_id=kwargs.get('community_id'),
            icon_url=kwargs.get('icon_url'),
            custom_time=kwargs.get('custom_time'),
            week_days=kwargs.get('week_days'),
            custom_start_date=kwargs.get('custom_start_date'),
            custom_end_date=kwargs.get('custom_end_date')
        )

    @property
    def is_enabled(self) -> bool:
        """规则是否启用"""
        return self.status == 1

    @property
    def is_deleted(self) -> bool:
        """规则是否已删除"""
        return self.status == 2

    def enable(self) -> None:
        """启用规则"""
        self.status = 1
        self.updated_at = datetime.now()

    def disable(self) -> None:
        """禁用规则"""
        self.status = 0
        self.updated_at = datetime.now()

    def soft_delete(self) -> None:
        """软删除规则"""
        self.status = 2
        self.updated_at = datetime.now()

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
        if name is not None and len(name.strip()) > 0:
            self.rule_name = name.strip()[:100]

        if frequency_type is not None and frequency_type in [0, 1, 2]:
            self.frequency_type = frequency_type

        if time_slot_type is not None and time_slot_type in [0, 1, 2, 3, 4]:
            self.time_slot_type = time_slot_type

        if custom_time is not None:
            # 验证时间格式 HH:MM:SS
            try:
                time.fromisoformat(custom_time)
                self.custom_time = custom_time
            except ValueError:
                pass  # 忽略无效的时间格式

        if icon_url is not None:
            if icon_url.startswith(('http://', 'https://')) and len(icon_url) <= 500:
                self.icon_url = icon_url.strip()

        self.updated_at = datetime.now()

    def calculate_planned_checkin_time(self, reference_date: Optional[datetime] = None) -> Optional[datetime]:
        """
        计算计划的打卡时间

        Args:
            reference_date: 参考日期(默认为今天)

        Returns:
            计划打卡时间,如果无法计算则返回 None
        """
        if reference_date is None:
            reference_date = datetime.now()

        if not self.is_enabled or self.is_deleted:
            return None

        # 自定义时间 (custom_time 可能是字符串或 time 对象)
        if self.time_slot_type == 4 and self.custom_time:
            try:
                if isinstance(self.custom_time, str):
                    time_obj = time.fromisoformat(self.custom_time)
                    return datetime.combine(reference_date.date(), time_obj)
                elif isinstance(self.custom_time, time):
                    return datetime.combine(reference_date.date(), self.custom_time)
            except (ValueError, TypeError):
                return None

        # 预定义时间段
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
        return self.rule_id == other.rule_id

    def __hash__(self) -> int:
        return hash(self.rule_id)
