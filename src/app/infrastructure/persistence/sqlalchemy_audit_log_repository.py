"""
SQLAlchemy 审计日志仓储实现
"""
from typing import List
from sqlalchemy import select

from app.domain.repositories.audit_log_repository import AuditLogRepository
from database.flask_models import db, UserAuditLog


class SQLAlchemyAuditLogRepository(AuditLogRepository):
    """SQLAlchemy 审计日志仓储实现"""

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
        audit_log = UserAuditLog(
            user_id=user_id,
            action=action,
            detail=detail,
            **kwargs
        )
        db.session.add(audit_log)
        db.session.flush()
        return audit_log

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
        stmt = select(UserAuditLog).where(
            UserAuditLog.user_id == user_id
        ).order_by(
            UserAuditLog.created_at.desc()
        ).limit(limit).offset(offset)

        return list(db.session.execute(stmt).scalars().all())

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
        stmt = select(UserAuditLog).where(
            UserAuditLog.action == action
        ).order_by(
            UserAuditLog.created_at.desc()
        ).limit(limit).offset(offset)

        return list(db.session.execute(stmt).scalars().all())