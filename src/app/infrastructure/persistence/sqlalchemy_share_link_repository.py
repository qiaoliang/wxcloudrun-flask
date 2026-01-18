"""
分享链接仓储 - SQLAlchemy 实现
"""
from typing import List, Optional

from sqlalchemy import select, delete

from database.flask_models import db, ShareLink
from app.domain.repositories.share_link_repository import ShareLinkRepository


class SQLAlchemyShareLinkRepository(ShareLinkRepository):
    """分享链接仓储 - SQLAlchemy 实现"""

    def find_by_id(self, link_id: int) -> Optional[ShareLink]:
        """
        根据ID查找分享链接

        Args:
            link_id: 分享链接ID

        Returns:
            Optional[ShareLink]: 分享链接对象，不存在时返回None
        """
        return db.session.get(ShareLink, link_id)

    def find_by_token(self, token: str) -> Optional[ShareLink]:
        """
        根据token查找分享链接

        Args:
            token: 分享链接token

        Returns:
            Optional[ShareLink]: 分享链接对象，不存在时返回None
        """
        stmt = select(ShareLink).filter_by(token=token)
        return db.session.execute(stmt).scalar_one_or_none()

    def find_by_user_id(self, user_id: int) -> List[ShareLink]:
        """
        根据用户ID查找分享链接列表

        Args:
            user_id: 用户ID

        Returns:
            List[ShareLink]: 分享链接列表
        """
        stmt = select(ShareLink).filter_by(solo_user_id=user_id)
        return db.session.execute(stmt).scalars().all()

    def save(self, entity: ShareLink) -> ShareLink:
        """
        保存分享链接

        Args:
            entity: 分享链接对象

        Returns:
            ShareLink: 保存后的分享链接对象（不提交事务，由 UseCase 层管理）
        """
        db.session.add(entity)
        db.session.flush()
        return entity

    def update(self, entity: ShareLink) -> ShareLink:
        """
        更新分享链接

        Args:
            entity: 分享链接对象

        Returns:
            ShareLink: 更新后的分享链接对象（不提交事务，由 UseCase 层管理）
        """
        db.session.merge(entity)
        db.session.flush()
        return entity

    def delete(self, link_id: int) -> bool:
        """
        删除分享链接

        Args:
            link_id: 分享链接ID

        Returns:
            bool: 删除是否成功（不提交事务，由 UseCase 层管理）
        """
        stmt = delete(ShareLink).where(ShareLink.link_id == link_id)
        result = db.session.execute(stmt)
        return result.rowcount > 0
