"""
SQLAlchemy 社区申请仓储实现
"""
from typing import List, Optional
from sqlalchemy import select

from app.domain.repositories.community_application_repository import CommunityApplicationRepository
from database.flask_models import db, CommunityApplication


class SQLAlchemyCommunityApplicationRepository(CommunityApplicationRepository):
    """SQLAlchemy 社区申请仓储实现"""

    def save(self, application: CommunityApplication) -> CommunityApplication:
        """
        保存社区申请

        Args:
            application: 社区申请实体

        Returns:
            CommunityApplication: 保存后的社区申请
        """
        db.session.add(application)
        db.session.flush()
        return application

    def find_by_id(self, application_id: int) -> Optional[CommunityApplication]:
        """
        根据ID查找社区申请

        Args:
            application_id: 申请ID

        Returns:
            Optional[CommunityApplication]: 社区申请，不存在返回 None
        """
        return db.session.get(CommunityApplication, application_id)

    def find_pending_by_user_and_community(
        self, user_id: int, community_id: int
    ) -> Optional[CommunityApplication]:
        """
        查找用户对社区的待审核申请

        Args:
            user_id: 用户ID
            community_id: 社区ID

        Returns:
            Optional[CommunityApplication]: 待审核申请，不存在返回 None
        """
        stmt = select(CommunityApplication).where(
            CommunityApplication.user_id == user_id,
            CommunityApplication.target_community_id == community_id,
            CommunityApplication.status == 1  # 待审核
        )
        return db.session.execute(stmt).scalar_one_or_none()

    def find_by_community(
        self, community_id: int, status: Optional[int] = None
    ) -> List[CommunityApplication]:
        """
        查找社区的所有申请

        Args:
            community_id: 社区ID
            status: 申请状态（可选）

        Returns:
            List[CommunityApplication]: 申请列表
        """
        stmt = select(CommunityApplication).where(
            CommunityApplication.target_community_id == community_id
        )

        if status is not None:
            stmt = stmt.where(CommunityApplication.status == status)

        stmt = stmt.order_by(CommunityApplication.created_at.desc())
        return list(db.session.execute(stmt).scalars().all())

    def update_status(
        self,
        application_id: int,
        status: int,
        processor_id: int,
        rejection_reason: Optional[str] = None
    ) -> Optional[CommunityApplication]:
        """
        更新申请状态

        Args:
            application_id: 申请ID
            status: 新状态
            processor_id: 处理者ID
            rejection_reason: 拒绝理由（可选）

        Returns:
            Optional[CommunityApplication]: 更新后的申请，不存在返回 None
        """
        from datetime import datetime

        application = self.find_by_id(application_id)
        if not application:
            return None

        application.status = status
        application.processed_by = processor_id
        application.updated_at = datetime.now()

        if rejection_reason:
            application.rejection_reason = rejection_reason

        db.session.flush()
        return application