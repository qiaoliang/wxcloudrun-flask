"""
个人资料查看日志仓储 SQLAlchemy 实现
"""
from typing import List, Optional
from datetime import datetime, timedelta

from sqlalchemy import select, and_
from database.flask_models import db, ProfileViewLog
from app.domain.repositories.profile_view_log_repository import ProfileViewLogRepository


class SQLAlchemyProfileViewLogRepository(ProfileViewLogRepository):
    """个人资料查看日志仓储 SQLAlchemy 实现"""

    def find_by_id(self, log_id: int) -> Optional[ProfileViewLog]:
        """
        根据ID查找查看日志

        Args:
            log_id: 日志ID

        Returns:
            个人资料查看日志对象，如果不存在则返回 None
        """
        return db.session.get(ProfileViewLog, log_id)

    def find_by_viewer_id(self, viewer_id: int, limit: int = 100) -> List[ProfileViewLog]:
        """
        根据查看者ID查找查看日志

        Args:
            viewer_id: 查看者ID
            limit: 返回数量限制

        Returns:
            个人资料查看日志列表
        """
        query = select(ProfileViewLog).where(
            ProfileViewLog.viewer_id == viewer_id
        ).order_by(ProfileViewLog.created_at.desc()).limit(limit)

        result = db.session.execute(query)
        return list(result.scalars().all())

    def find_by_viewed_user_id(self, viewed_user_id: int, limit: int = 100) -> List[ProfileViewLog]:
        """
        根据被查看者ID查找查看日志

        Args:
            viewed_user_id: 被查看者ID
            limit: 返回数量限制

        Returns:
            个人资料查看日志列表
        """
        query = select(ProfileViewLog).where(
            ProfileViewLog.viewed_user_id == viewed_user_id
        ).order_by(ProfileViewLog.created_at.desc()).limit(limit)

        result = db.session.execute(query)
        return list(result.scalars().all())

    def find_by_community_id(self, community_id: int, limit: int = 100) -> List[ProfileViewLog]:
        """
        根据社区ID查找查看日志

        Args:
            community_id: 社区ID
            limit: 返回数量限制

        Returns:
            个人资料查看日志列表
        """
        query = select(ProfileViewLog).where(
            ProfileViewLog.community_id == community_id
        ).order_by(ProfileViewLog.created_at.desc()).limit(limit)

        result = db.session.execute(query)
        return list(result.scalars().all())

    def find_by_viewer_and_viewed(self, viewer_id: int, viewed_user_id: int,
                                  limit: int = 100) -> List[ProfileViewLog]:
        """
        根据查看者和被查看者查找查看日志

        Args:
            viewer_id: 查看者ID
            viewed_user_id: 被查看者ID
            limit: 返回数量限制

        Returns:
            个人资料查看日志列表
        """
        query = select(ProfileViewLog).where(
            ProfileViewLog.viewer_id == viewer_id,
            ProfileViewLog.viewed_user_id == viewed_user_id
        ).order_by(ProfileViewLog.created_at.desc()).limit(limit)

        result = db.session.execute(query)
        return list(result.scalars().all())

    def save(self, log: ProfileViewLog) -> ProfileViewLog:
        """
        保存个人资料查看日志

        Args:
            log: 个人资料查看日志对象

        Returns:
            保存后的个人资料查看日志对象
        """
        db.session.add(log)
        db.session.flush()
        return log

    def delete(self, log_id: int) -> bool:
        """
        删除个人资料查看日志

        Args:
            log_id: 日志ID

        Returns:
            是否删除成功
        """
        log = self.find_by_id(log_id)
        if log:
            db.session.delete(log)
            db.session.flush()
            return True
        return False

    def count_by_viewer_id(self, viewer_id: int) -> int:
        """
        统计查看者的查看次数

        Args:
            viewer_id: 查看者ID

        Returns:
            查看次数
        """
        from sqlalchemy import func

        query = select(func.count(ProfileViewLog.id)).where(
            ProfileViewLog.viewer_id == viewer_id
        )

        result = db.session.execute(query)
        return result.scalar() or 0

    def count_by_viewed_user_id(self, viewed_user_id: int) -> int:
        """
        统计被查看者的被查看次数

        Args:
            viewed_user_id: 被查看者ID

        Returns:
            被查看次数
        """
        from sqlalchemy import func

        query = select(func.count(ProfileViewLog.id)).where(
            ProfileViewLog.viewed_user_id == viewed_user_id
        )

        result = db.session.execute(query)
        return result.scalar() or 0

    def get_recent_views_by_community(self, community_id: int, days: int = 7) -> List[ProfileViewLog]:
        """
        获取社区最近N天的查看记录

        Args:
            community_id: 社区ID
            days: 天数

        Returns:
            个人资料查看日志列表
        """
        start_date = datetime.now() - timedelta(days=days)

        query = select(ProfileViewLog).where(
            ProfileViewLog.community_id == community_id,
            ProfileViewLog.created_at >= start_date
        ).order_by(ProfileViewLog.created_at.desc())

        result = db.session.execute(query)
        return list(result.scalars().all())

    def delete_old_logs(self, days: int = 90) -> int:
        """
        删除N天前的旧日志

        Args:
            days: 天数

        Returns:
            删除的日志数量
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        query = select(ProfileViewLog).where(
            ProfileViewLog.created_at < cutoff_date
        )

        result = db.session.execute(query)
        logs = result.scalars().all()

        for log in logs:
            db.session.delete(log)

        db.session.flush()
        return len(logs)