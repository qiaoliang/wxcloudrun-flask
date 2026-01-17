"""
打卡记录领域实体

纯领域实体,不依赖 ORM 模型,遵循 DDD 原则
"""
from typing import Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum


class CheckinStatus(Enum):
    """打卡状态枚举"""
    PENDING = 0  # 未打卡
    COMPLETED = 1  # 已打卡
    MISSED = 2  # 已错过
    CANCELLED = 3  # 已取消


@dataclass
class CheckinRecordEntity:
    """
    打卡记录领域实体

    这是一个纯领域实体,不依赖任何 ORM 框架。
    """
    # 基础属性
    record_id: int
    rule_id: int
    user_id: int
    planned_checkin_time: datetime

    # 状态
    checkin_status: int = CheckinStatus.PENDING.value

    # 可选属性
    community_rule_id: Optional[int] = None
    solo_user_id: Optional[int] = None  # 监督用户ID
    checkin_time: Optional[datetime] = None

    # 时间戳
    created_at: Optional[datetime] = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = field(default_factory=datetime.now)

    # 领域事件
    _events: list = field(default_factory=list, init=False, repr=False)

    @classmethod
    def create(cls, record_id: int, rule_id: int, user_id: int,
              planned_checkin_time: datetime, **kwargs) -> 'CheckinRecordEntity':
        """
        工厂方法:创建打卡记录实体

        Args:
            record_id: 记录ID
            rule_id: 个人规则ID
            user_id: 用户ID
            planned_checkin_time: 计划打卡时间
            **kwargs: 其他可选属性

        Returns:
            CheckinRecordEntity: 打卡记录实体
        """
        return cls(
            record_id=record_id,
            rule_id=rule_id,
            user_id=user_id,
            planned_checkin_time=planned_checkin_time,
            community_rule_id=kwargs.get('community_rule_id'),
            solo_user_id=kwargs.get('solo_user_id'),
            checkin_status=kwargs.get('checkin_status', CheckinStatus.PENDING.value),
            checkin_time=kwargs.get('checkin_time')
        )

    @property
    def is_completed(self) -> bool:
        """是否已完成"""
        return self.checkin_status == CheckinStatus.COMPLETED.value

    @property
    def is_missed(self) -> bool:
        """是否已错过"""
        return self.checkin_status == CheckinStatus.MISSED.value

    @property
    def is_cancelled(self) -> bool:
        """是否已取消"""
        return self.checkin_status == CheckinStatus.CANCELLED.value

    @property
    def actual_checkin_time(self) -> Optional[datetime]:
        """获取实际打卡时间"""
        return self.checkin_time

    def complete(self, checkin_time: Optional[datetime] = None) -> None:
        """
        完成打卡

        Args:
            checkin_time: 打卡时间(默认为当前时间)
        """
        if checkin_time is None:
            checkin_time = datetime.now()

        self.checkin_status = CheckinStatus.COMPLETED.value
        self.checkin_time = checkin_time
        self.updated_at = datetime.now()

    def mark_missed(self) -> None:
        """标记为错过"""
        self.checkin_status = CheckinStatus.MISSED.value
        self.updated_at = datetime.now()

    def cancel(self) -> None:
        """取消打卡"""
        self.checkin_status = CheckinStatus.CANCELLED.value
        self.updated_at = datetime.now()

    def update_checkin_time(self, checkin_time: datetime) -> None:
        """
        更新打卡时间

        Args:
            checkin_time: 打卡时间
        """
        self.checkin_time = checkin_time
        self.updated_at = datetime.now()

    def is_overdue(self, reference_time: Optional[datetime] = None) -> bool:
        """
        检查是否已超时

        Args:
            reference_time: 参考时间(默认为当前时间)

        Returns:
            bool: 是否已超时
        """
        if reference_time is None:
            reference_time = datetime.now()

        # 超过计划打卡时间4小时视为超时
        overdue_threshold = timedelta(hours=4)
        return reference_time > (self.planned_checkin_time + overdue_threshold)

    def get_checkin_delay(self) -> Optional[timedelta]:
        """
        获取打卡延迟时间

        Returns:
            延迟时间,如果未打卡或已取消则返回 None
        """
        if not self.is_completed or self.checkin_time is None:
            return None

        return self.checkin_time - self.planned_checkin_time

    def __eq__(self, other) -> bool:
        if not isinstance(other, CheckinRecordEntity):
            return False
        return self.record_id == other.record_id

    def __hash__(self) -> int:
        return hash(self.record_id)
