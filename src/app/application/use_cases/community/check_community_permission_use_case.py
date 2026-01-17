"""
检查社区权限用例
"""
import logging
from sqlalchemy import select
from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.domain.repositories.community_repository import CommunityRepository
from app.domain.repositories.user_repository import UserRepository


class CheckCommunityPermissionUseCase(BaseUseCase):
    """检查社区权限用例"""

    def __init__(self):
        super().__init__()
        self.community_repository = RepositoryFactory.get_community_repository()
        self.user_repository = RepositoryFactory.get_user_repository()
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
            stmt = select(User).where(User.user_id == user_id)
            user = db.session.execute(stmt).scalar_one_or_none()

            if not user:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='用户不存在'
                )

            # 3. 检查权限
            # 超级管理员可以访问所有社区
            if user.role == 4:  # SUPER_ADMIN
                has_permission = True
            # 社区主管和专员可以访问自己所属的社区
            elif user.community_id == community_id and user.role in [2, 3]:  # MANAGER, STAFF
                has_permission = True
            else:
                has_permission = False

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