"""
从社区移除用户用例
"""

from app.application.use_cases.base import BaseUseCase, UseCaseResult
from database.flask_models import db, User


class RemoveUserFromCommunityUseCase(BaseUseCase):
    """从社区移除用户用例"""

    def execute(self, community_id: int, target_user_id: int) -> UseCaseResult:
        """
        从社区移除用户

        Args:
            community_id: 社区ID
            target_user_id: 目标用户ID

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            if not community_id or not target_user_id:
                return UseCaseResult.fail("参数不能为空")

            # 查询用户
            stmt = db.session.execute(
                db.select(User).where(User.user_id == target_user_id)
            )
            user = stmt.scalar_one_or_none()

            if not user:
                return UseCaseResult.fail("用户不存在")

            # 检查用户是否属于该社区
            if user.community_id != community_id:
                return UseCaseResult.fail("用户不属于该社区")

            # 移除用户（将 community_id 设为 None）
            user.community_id = None
            db.session.commit()

            return UseCaseResult.success({
                'user_id': target_user_id,
                'community_id': community_id
            }, "移除用户成功")

        except Exception as e:
            db.session.rollback()
            return UseCaseResult.fail(f"移除用户失败: {str(e)}")