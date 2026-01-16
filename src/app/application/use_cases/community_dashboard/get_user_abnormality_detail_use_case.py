"""
获取用户异常值详情用例
"""
from app.application.use_cases.base import BaseUseCase, UseCaseResult, UseCaseStatus
from app.infrastructure.persistence.repository_factory import RepositoryFactory


class GetUserAbnormalityDetailUseCase(BaseUseCase):
    """获取用户异常详情用例"""

    def __init__(self):
        """初始化用例，注入依赖的仓储"""
        self.dashboard_repository = RepositoryFactory.get_community_dashboard_repository()

    def _validate(self, community_id: int, user_id: int, request_user_id: int) -> UseCaseResult:
        """
        验证输入参数

        Args:
            community_id: 社区ID
            user_id: 用户ID（要查询的用户）
            request_user_id: 请求用户ID（用于权限检查）

        Returns:
            UseCaseResult: 验证结果
        """
        if not community_id or community_id <= 0:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='社区ID无效'
            )

        if not user_id or user_id <= 0:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='用户ID无效'
            )

        if not request_user_id or request_user_id <= 0:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='请求用户ID无效'
            )

        # 检查权限
        if not self.dashboard_repository.has_permission(request_user_id, community_id):
            return UseCaseResult(
                status=UseCaseStatus.FORBIDDEN,
                message='无权限访问该社区'
            )

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message="验证通过"
        )

    def _execute(self, community_id: int, user_id: int, request_user_id: int) -> UseCaseResult:
        """
        执行获取用户异常详情操作

        Args:
            community_id: 社区ID
            user_id: 用户ID（要查询的用户）
            request_user_id: 请求用户ID（用于权限检查）

        Returns:
            UseCaseResult: 执行结果
        """
        # 获取用户异常详情
        detail = self.dashboard_repository.get_user_abnormality_detail(community_id, user_id)

        import logging
        logger = logging.getLogger(__name__)
        logger.info(f'获取用户异常详情成功: community_id={community_id}, user_id={user_id}')
        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message='获取用户异常详情成功',
            data=detail
        )
