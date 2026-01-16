"""
验证用户社区访问权限用例
"""

from app.application.use_cases.base import BaseUseCase, UseCaseResult, UseCaseStatus
from database.flask_models import db, User
from sqlalchemy import select


class VerifyUserCommunityAccessUseCase(BaseUseCase):
    """验证用户社区访问权限用例"""

    def execute(self, user_id: int, community_id: int) -> UseCaseResult:
        """
        验证用户是否有访问社区的权限

        Args:
            user_id: 用户ID
            community_id: 社区ID

        Returns:
            UseCaseResult: 包含权限验证结果
        """
        try:
            if not user_id or not community_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message="参数不能为空"
                )

            # 查询用户
            stmt = db.session.execute(
                db.select(User).where(User.user_id == user_id)
            )
            user = stmt.scalar_one_or_none()

            if not user:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message="用户不存在"
                )

            # 检查用户是否属于该社区
            has_access = user.community_id == community_id

            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message="权限验证完成",
                data={
                    'has_access': has_access,
                    'user_id': user_id,
                    'community_id': community_id
                }
            )

        except Exception as e:
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f"权限验证失败: {str(e)}"
            )
