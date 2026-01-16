"""
获取待处理事件列表用例
"""
from app.application.use_cases.base import BaseUseCase, UseCaseResult, UseCaseStatus
from app.infrastructure.persistence.repository_factory import RepositoryFactory


class GetPendingEventsUseCase(BaseUseCase):
    """获取待处理事件列表用例"""

    def __init__(self):
        """初始化用例，注入依赖的仓储"""
        self.dashboard_repository = RepositoryFactory.get_community_dashboard_repository()

    def _validate(self, community_id: int, user_id: int, limit: int = 3) -> UseCaseResult:
        """
        验证输入参数

        Args:
            community_id: 社区ID
            user_id: 用户ID
            limit: 最大返回数量

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

        if limit < 1 or limit > 50:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='限制数量必须在 1-50 之间'
            )

        # 检查权限
        if not self.dashboard_repository.has_permission(user_id, community_id):
            return UseCaseResult(
                status=UseCaseStatus.FORBIDDEN,
                message='无权限访问该社区'
            )

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message="验证通过"
        )

    def _execute(self, community_id: int, user_id: int, limit: int = 3) -> UseCaseResult:
        """
        执行获取待处理事件列表操作

        Args:
            community_id: 社区ID
            user_id: 用户ID
            limit: 最大返回数量

        Returns:
            UseCaseResult: 执行结果
        """
        # 获取待处理事件列表
        events = self.dashboard_repository.get_pending_events(community_id, limit)

        import logging
        logger = logging.getLogger(__name__)
        logger.info(
            f'获取待处理事件列表成功: community_id={community_id}, '
            f'count={len(events)}'
        )
        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message='获取待处理事件列表成功',
            data={
                'events': events,
                'total': len(events)
            }
        )
