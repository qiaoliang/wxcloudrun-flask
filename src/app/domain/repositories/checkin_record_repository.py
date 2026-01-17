"""
打卡记录仓储接口

仓储接口定义在领域层,遵循依赖倒置原则
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from app.domain.entities.checkin_record_entity import CheckinRecordEntity


class CheckinRecordRepository(ABC):
    """打卡记录仓储接口"""

    @abstractmethod
    def find_by_id(self, record_id: int) -> Optional[CheckinRecordEntity]:
        """
        根据ID查找打卡记录

        Args:
            record_id: 记录ID

        Returns:
            Optional[CheckinRecordEntity]: 领域实体,不存在返回 None
        """
        pass

    @abstractmethod
    def find_by_rule_id(self, rule_id: int) -> List[CheckinRecordEntity]:
        """
        根据规则ID查找打卡记录

        Args:
            rule_id: 规则ID

        Returns:
            List[CheckinRecordEntity]: 领域实体列表
        """
        pass

    @abstractmethod
    def find_by_user_id(self, user_id: int, limit: int = 100) -> List[CheckinRecordEntity]:
        """
        根据用户ID查找打卡记录

        Args:
            user_id: 用户ID
            limit: 返回数量限制

        Returns:
            List[CheckinRecordEntity]: 领域实体列表
        """
        pass

    @abstractmethod
    def find_today_records(self, user_id: int, rule_id: int) -> List[CheckinRecordEntity]:
        """
        查找用户今天对某个规则的打卡记录

        Args:
            user_id: 用户ID
            rule_id: 规则ID

        Returns:
            List[CheckinRecordEntity]: 领域实体列表
        """
        pass

    @abstractmethod
    def save_entity(self, entity: CheckinRecordEntity) -> CheckinRecordEntity:
        """
        保存打卡记录实体

        Args:
            entity: 打卡记录领域实体

        Returns:
            CheckinRecordEntity: 保存后的实体(包含生成的ID)
        """
        pass

    @abstractmethod
    def update_entity(self, entity: CheckinRecordEntity) -> CheckinRecordEntity:
        """
        更新打卡记录实体

        Args:
            entity: 打卡记录领域实体

        Returns:
            CheckinRecordEntity: 更新后的实体
        """
        pass

    @abstractmethod
    def delete(self, record_id: int) -> bool:
        """
        删除打卡记录

        Args:
            record_id: 记录ID

        Returns:
            bool: 是否删除成功
        """
        pass
