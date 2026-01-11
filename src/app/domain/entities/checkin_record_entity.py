"""
打卡记录领域实体

封装打卡记录相关的业务逻辑。
"""
from typing import Optional
from datetime import datetime, timedelta

from database.flask_models import CheckinRecord


class CheckinRecordEntity:
    """打卡记录领域实体"""

    def __init__(self, record: CheckinRecord):
        """
        初始化打卡记录领域实体

        Args:
            record: SQLAlchemy CheckinRecord 模型实例
        """
        self._record = record

    @property
    def record(self) -> CheckinRecord:
        """获取底层的 SQLAlchemy CheckinRecord 模型"""
        return self._record

    @property
    def record_id(self) -> int:
        """获取记录ID"""
        return self._record.record_id

    @property
    def user_id(self) -> int:
        """获取用户ID"""
        return self._record.user_id

    @property
    def rule_id(self) -> Optional[int]:
        """获取个人规则ID"""
        return self._record.rule_id

    @property
    def community_rule_id(self) -> Optional[int]:
        """获取社区规则ID"""
        return self._record.community_rule_id

    @property
    def is_completed(self) -> bool:
        """是否已完成"""
        return self._record.checkin_status == 1

    @property
    def is_missed(self) -> bool:
        """是否已错过"""
        return self._record.checkin_status == 2

    @property
    def is_cancelled(self) -> bool:
        """是否已取消"""
        return self._record.checkin_status == 3

    @property
    def planned_checkin_time(self) -> Optional[datetime]:
        """获取计划打卡时间"""
        return self._record.planned_checkin_time

    @property
    def actual_checkin_time(self) -> Optional[datetime]:
        """获取实际打卡时间"""
        return self._record.checkin_time

    @property
    def solo_user_id(self) -> Optional[int]:
        """获取监督用户ID（如果是监督打卡）"""
        return self._record.solo_user_id

    def complete(self, checkin_time: Optional[datetime] = None) -> None:
        """
        完成打卡

        Args:
            checkin_time: 打卡时间（默认为当前时间）
        """
        if checkin_time is None:
            checkin_time = datetime.now()

        self._record.checkin_status = 1
        self._record.checkin_time = checkin_time
        self._record.updated_at = datetime.now()

    def mark_missed(self) -> None:
        """标记为错过"""
        self._record.checkin_status = 2
        self._record.updated_at = datetime.now()

    def cancel(self) -> None:
        """取消打卡"""
        self._record.checkin_status = 3
        self._record.updated_at = datetime.now()

    def update_checkin_time(self, checkin_time: datetime) -> None:
        """
        更新打卡时间

        Args:
            checkin_time: 打卡时间
        """
        self._record.checkin_time = checkin_time
        self._record.updated_at = datetime.now()

    def is_overdue(self, reference_time: Optional[datetime] = None) -> bool:
        """
        检查是否已超时

        Args:
            reference_time: 参考时间（默认为当前时间）

        Returns:
            bool: 是否已超时
        """
        if reference_time is None:
            reference_time = datetime.now()

        if self._record.planned_checkin_time is None:
            return False

        # 超过计划打卡时间4小时视为超时
        overdue_threshold = timedelta(hours=4)
        return reference_time > (self._record.planned_checkin_time + overdue_threshold)

    def get_checkin_delay(self) -> Optional[timedelta]:
        """
        获取打卡延迟时间

        Returns:
            延迟时间，如果未打卡或已取消则返回 None
        """
        if not self.is_completed or self._record.checkin_time is None or self._record.planned_checkin_time is None:
            return None

        return self._record.checkin_time - self._record.planned_checkin_time

    def __eq__(self, other) -> bool:
        if not isinstance(other, CheckinRecordEntity):
            return False
        return self._record.record_id == other._record.record_id

    def __hash__(self) -> int:
        return hash(self._record.record_id)