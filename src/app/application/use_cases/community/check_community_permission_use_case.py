"""
检查社区权限用例
"""
import logging
from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from database.flask_models import db, User, Community


class CheckCommunityPermissionUseCase(BaseUseCase):
    """检查社区权限用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

    def execute(self, user_id: int, community_id: int) -> UseCaseResult:
        """
        执行检查社区权限用例

        Args:
            user_id: 用户ID
            community_id: 社区ID

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not user_id or not community_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='参数不能为空'
                )

            # 2. 查询用户
            stmt = db.session.execute(
                db.select(User).where(User.user_id == user_id)
            )
            user = stmt.scalar_one_or_none()

            if not user:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='用户不存在'
                )

            # 3. 检查权限
            has_permission = False
            if user.community_id == community_id:
                # 用户是该社区成员
                has_permission = True
            elif user.role in [2, 3]:  # 管理员或超级管理员
                # 管理员可以访问所有社区
                has_permission = True

            self.logger.info(f'检查社区权限: user_id={user_id}, community_id={community_id}, has_permission={has_permission}')

            # 4. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='权限检查完成',
                data={'has_permission': has_permission}
            )

        except Exception as e:
            self.logger.error(f'检查社区权限失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'权限检查失败: {str(e)}'
            )