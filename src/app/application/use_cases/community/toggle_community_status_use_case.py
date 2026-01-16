"""
切换社区状态用例
"""

from app.application.use_cases.base import BaseUseCase, UseCaseResult
from database.flask_models import db, Community
from sqlalchemy import select


class ToggleCommunityStatusUseCase(BaseUseCase):
    """切换社区状态用例"""

    def execute(self, community_id: int, status: int) -> UseCaseResult:
        """
        切换社区状态

        Args:
            community_id: 社区ID
            status: 状态 (1=正常, 0=禁用)

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            if not community_id or status is None:
                return UseCaseResult.fail("参数不能为空")

            # 查询社区
            stmt = db.session.execute(
                db.select(Community).where(Community.community_id == community_id)
            )
            community = stmt.scalar_one_or_none()

            if not community:
                return UseCaseResult.fail("社区不存在")

            # 更新状态
            community.status = status
            db.session.commit()

            return UseCaseResult.success({
                'community_id': community_id,
                'status': status
            }, "状态更新成功")

        except Exception as e:
            db.session.rollback()
            return UseCaseResult.fail(f"状态更新失败: {str(e)}")