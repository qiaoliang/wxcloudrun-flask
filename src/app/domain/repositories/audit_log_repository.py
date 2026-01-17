"""
审计日志仓储接口
"""
from typing import List, Optional
from abc import ABC, abstractmethod

from database.flask_models import UserAuditLog


class AuditLogRepository(ABC):
    """审计日志仓储接口"""

    @abstractmethod
    def create(
        self,
        user_id: int,
        action: str,
        detail: str,
        **kwargs
    ) -> UserAuditLog:
        """
        创建审计日志

        Args:
            user_id: 用户ID
            action: 操作类型
            detail: 操作详情
            **kwargs: 其他字段

        Returns:
            UserAuditLog: 创建的审计日志
        """
        pass

    @abstractmethod
    def find_by_user_id(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> List[UserAuditLog]:
        """
        查找用户的审计日志

        Args:
            user_id: 用户ID
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            List[UserAuditLog]: 审计日志列表
        """
        pass

    @abstractmethod
    def find_by_action(
        self,
        action: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[UserAuditLog]:
        """
        根据操作类型查找审计日志

        Args:
            action: 操作类型
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            List[UserAuditLog]: 审计日志列表
        """
        pass