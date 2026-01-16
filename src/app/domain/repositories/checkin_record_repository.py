"""
打卡记录仓储接口
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime, date

from database.flask_models import CheckinRecord


class CheckinRecordRepository(ABC):
    """打卡记录仓储接口"""

    @abstractmethod
    def find_by_id(self, record_id: int) -> Optional[CheckinRecord]:
        """根据ID查找打卡记录"""
        pass

    @abstractmethod
    def find_by_user_id(
        self, 
        user_id: int, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None
    ) -> List[CheckinRecord]:
        """根据用户ID查找打卡记录"""
        pass

    @abstractmethod
    def find_by_rule_id(
        self, 
        rule_id: int, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None
    ) -> List[CheckinRecord]:
        """根据规则ID查找打卡记录"""
        pass

    @abstractmethod
    def find_today_records(self, user_id: int) -> List[CheckinRecord]:
        """查找用户今日的打卡记录"""
        pass

    @abstractmethod
    def find_missed_records(
        self, 
        user_id: int, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None
    ) -> List[CheckinRecord]:
        """查找用户漏打卡记录"""
        pass

    @abstractmethod
    def save(self, record: CheckinRecord) -> CheckinRecord:
        """保存打卡记录"""
        pass

    @abstractmethod
    def update(self, record: CheckinRecord) -> CheckinRecord:
        """更新打卡记录"""
        pass

    @abstractmethod
    def delete(self, record_id: int) -> bool:
        """删除打卡记录"""
        pass

    @abstractmethod
    def cancel(self, record_id: int) -> bool:
        """取消打卡记录"""
        pass

    @abstractmethod
    def count_by_user_id(self, user_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None) -> int:
        """统计用户打卡记录数量"""
        pass

    @abstractmethod
    def find_by_rule_and_date(self, rule_id: int, check_date: date, rule_source: str = 'personal') -> List[CheckinRecord]:
        """根据规则ID和日期查询打卡记录"""
        pass

    @abstractmethod
    def find_by_community_rule_and_users(
        self,
        community_rule_id: int,
        user_ids: List[int],
        planned_time: datetime
    ) -> List[CheckinRecord]:
        """根据社区规则ID和用户列表查询打卡记录"""
        pass

    @abstractmethod
    def create(
        self,
        rule_id: int,
        user_id: int,
        checkin_time: Optional[datetime],
        planned_time: datetime,
        status: int,
        rule_source: str = 'personal'
    ) -> CheckinRecord:
        """创建打卡记录"""
        pass