"""
打卡规则仓储接口

仓储接口定义在领域层,遵循依赖倒置原则
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from app.domain.entities.checkin_rule_entity import CheckinRuleEntity


class CheckinRuleRepository(ABC):
    """打卡规则仓储接口"""

    @abstractmethod
    def find_by_id(self, rule_id: int) -> Optional[CheckinRuleEntity]:
        """
        根据ID查找打卡规则

        Args:
            rule_id: 规则ID

        Returns:
            Optional[CheckinRuleEntity]: 领域实体,不存在返回 None
        """
        pass

    @abstractmethod
    def find_by_user_id(self, user_id: int, include_disabled: bool = False) -> List[CheckinRuleEntity]:
        """
        根据用户ID查找打卡规则

        Args:
            user_id: 用户ID
            include_disabled: 是否包含禁用的规则

        Returns:
            List[CheckinRuleEntity]: 领域实体列表
        """
        pass

    @abstractmethod
    def find_active_by_user_id(self, user_id: int) -> List[CheckinRuleEntity]:
        """
        根据用户ID查找启用的打卡规则

        Args:
            user_id: 用户ID

        Returns:
            List[CheckinRuleEntity]: 领域实体列表
        """
        pass

    @abstractmethod
    def save_entity(self, entity: CheckinRuleEntity) -> CheckinRuleEntity:
        """
        保存打卡规则实体

        Args:
            entity: 打卡规则领域实体

        Returns:
            CheckinRuleEntity: 保存后的实体(包含生成的ID)
        """
        pass

    @abstractmethod
    def update_entity(self, entity: CheckinRuleEntity) -> CheckinRuleEntity:
        """
        更新打卡规则实体

        Args:
            entity: 打卡规则领域实体

        Returns:
            CheckinRuleEntity: 更新后的实体
        """
        pass

    @abstractmethod
    def delete(self, rule_id: int) -> bool:
        """
        删除打卡规则

        Args:
            rule_id: 规则ID

        Returns:
            bool: 是否删除成功
        """
        pass

    @abstractmethod
    def soft_delete(self, rule_id: int) -> bool:
        """
        软删除打卡规则

        Args:
            rule_id: 规则ID

        Returns:
            bool: 是否删除成功
        """
        pass

    @abstractmethod
    def find_active_rules(self) -> List[CheckinRuleEntity]:
        """
        查找所有启用的打卡规则

        Returns:
            List[CheckinRuleEntity]: 领域实体列表
        """
        pass

    @abstractmethod
    def find_all_day_rules(self) -> List[CheckinRuleEntity]:
        """
        查找所有启用的全天打卡规则

        Returns:
            List[CheckinRuleEntity]: 领域实体列表
        """
        pass

    @abstractmethod
    def find_by_ids(self, rule_ids: List[int]) -> List[CheckinRuleEntity]:
        """
        根据ID列表查找打卡规则

        Args:
            rule_ids: 规则ID列表

        Returns:
            List[CheckinRuleEntity]: 领域实体列表
        """
        pass
