"""
分享链接访问日志仓储 - SQLAlchemy 实现
"""
from typing import List

from sqlalchemy import select

from database.flask_models import db, ShareLinkAccessLog
from app.domain.repositories.share_link_access_log_repository import ShareLinkAccessLogRepository


class SQLAlchemyShareLinkAccessLogRepository(ShareLinkAccessLogRepository):
    """分享链接访问日志仓储 - SQLAlchemy 实现"""

    def save(self, entity: ShareLinkAccessLog) -> ShareLinkAccessLog:
        """
        保存分享链接访问日志

        Args:
            entity: 分享链接访问日志对象

        Returns:
            ShareLinkAccessLog: 保存后的分享链接访问日志对象（不提交事务，由 UseCase 层管理）
        """
        db.session.add(entity)
        db.session.flush()
        return entity

    def find_by_token(self, token: str) -> List[ShareLinkAccessLog]:
        """
        根据token查找访问日志列表

        Args:
            token: 分享链接token

        Returns:
            List[ShareLinkAccessLog]: 访问日志列表
        """
        stmt = select(ShareLinkAccessLog).filter_by(token=token)
        return db.session.execute(stmt).scalars().all()
