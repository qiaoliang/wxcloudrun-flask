"""
打卡规则仓储接口
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from database.flask_models import CheckinRule


class CheckinRuleRepository(ABC):
    """打卡规则仓储接口"""

    @abstractmethod
    def find_by_id(self, rule_id: int) -> Optional[CheckinRule]:
        """根据ID查找打卡规则"""
        pass

    @abstractmethod
    def find_by_user_id(self, user_id: int, include_disabled: bool = False) -> List[CheckinRule]:
        """根据用户ID查找打卡规则"""
        pass

    @abstractmethod
    def find_active_by_user_id(self, user_id: int) -> List[CheckinRule]:
        """根据用户ID查找启用的打卡规则"""
        pass

    @abstractmethod
    def save(self, rule: CheckinRule) -> CheckinRule:
        """保存打卡规则"""
        pass

    @abstractmethod
    def update(self, rule: CheckinRule) -> CheckinRule:
        """更新打卡规则"""
        pass

    @abstractmethod
    def delete(self, rule_id: int) -> bool:
        """删除打卡规则"""
        pass

    @abstractmethod
    def soft_delete(self, rule_id: int) -> bool:
        """软删除打卡规则"""
        pass

    @abstractmethod
    def find_active_rules(self) -> List[CheckinRule]:
        """查找所有启用的打卡规则"""
        pass

    @abstractmethod
    def find_all_day_rules(self) -> List[CheckinRule]:
        """查找所有启用的全天打卡规则"""
        pass