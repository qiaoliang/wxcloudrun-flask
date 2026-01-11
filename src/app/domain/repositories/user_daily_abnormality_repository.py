"""
用户每日异常值仓储接口
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import date, datetime

from database.flask_models import UserDailyAbnormality


class UserDailyAbnormalityRepository(ABC):
    """用户每日异常值仓储接口"""

    @abstractmethod
    def find_by_id(self, abnormality_id: int) -> Optional[UserDailyAbnormality]:
        """
        根据ID查找异常记录

        Args:
            abnormality_id: 异常记录ID

        Returns:
            用户每日异常值对象，如果不存在则返回 None
        """
        pass

    @abstractmethod
    def find_by_user_id_and_date(self, user_id: int, date: date) -> List[UserDailyAbnormality]:
        """
        根据用户ID和日期查找异常记录

        Args:
            user_id: 用户ID
            date: 日期

        Returns:
            用户每日异常值列表
        """
        pass

    @abstractmethod
    def find_by_user_id_and_date_range(self, user_id: int, start_date: date, end_date: date) -> List[UserDailyAbnormality]:
        """
        根据用户ID和日期范围查找异常记录

        Args:
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            用户每日异常值列表
        """
        pass

    @abstractmethod
    def find_by_rule_id_and_date(self, rule_id: int, date: date) -> List[UserDailyAbnormality]:
        """
        根据规则ID和日期查找异常记录

        Args:
            rule_id: 规则ID
            date: 日期

        Returns:
            用户每日异常值列表
        """
        pass

    @abstractmethod
    def find_by_user_rule_and_date(self, user_id: int, rule_id: int, date: date) -> Optional[UserDailyAbnormality]:
        """
        根据用户ID、规则ID和日期查找异常记录

        Args:
            user_id: 用户ID
            rule_id: 规则ID
            date: 日期

        Returns:
            用户每日异常值对象，如果不存在则返回 None
        """
        pass

    @abstractmethod
    def save(self, abnormality: UserDailyAbnormality) -> UserDailyAbnormality:
        """
        保存用户每日异常值

        Args:
            abnormality: 用户每日异常值对象

        Returns:
            保存后的用户每日异常值对象
        """
        pass

    @abstractmethod
    def update_abnormality(self, user_id: int, rule_id: int, date: date,
                          abnormality_delta: int, checkin_time: datetime = None,
                          scheduled_time: datetime = None, is_completed: bool = None) -> Optional[UserDailyAbnormality]:
        """
        更新用户每日异常值

        Args:
            user_id: 用户ID
            rule_id: 规则ID
            date: 日期
            abnormality_delta: 异常值增量
            checkin_time: 打卡时间
            scheduled_time: 计划打卡时间
            is_completed: 是否已完成

        Returns:
            更新后的用户每日异常值对象，如果不存在则返回 None
        """
        pass

    @abstractmethod
    def get_abnormal_users_by_date(self, community_id: int, date: date, threshold: int = 5) -> List[int]:
        """
        获取指定日期异常值超过阈值的用户ID列表

        Args:
            community_id: 社区ID
            date: 日期
            threshold: 异常值阈值

        Returns:
            用户ID列表
        """
        pass

    @abstractmethod
    def get_user_abnormality_trend(self, user_id: int, days: int) -> List[dict]:
        """
        获取用户最近N天的异常值趋势

        Args:
            user_id: 用户ID
            days: 天数

        Returns:
            异常值趋势数据列表
        """
        pass

    @abstractmethod
    def delete_by_user_id(self, user_id: int) -> bool:
        """
        删除用户的所有异常记录

        Args:
            user_id: 用户ID

        Returns:
            是否删除成功
        """
        pass