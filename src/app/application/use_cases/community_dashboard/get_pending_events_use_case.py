"""
获取未处理事件列表用例
"""
from flask import current_app
from wxcloudrun.community_dashboard_service import CommunityDashboardService
from app.application.use_cases.base import BaseUseCase, UseCaseResult, UseCaseStatus


class GetPendingEventsUseCase(BaseUseCase):
    """获取未处理事件列表用例"""

    def _validate(self, community_id: int, user_id: int, limit: int = 3) -> UseCaseResult:
        """
        验证输入参数

        Args:
            community_id: 社区ID
            user_id: 用户ID
            limit: 最大返回数量（默认3）

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

        if limit < 1 or limit > 100:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='限制数量必须在 1-100 之间'
            )

        # 检查权限
        if not CommunityDashboardService.has_permission(user_id, community_id):
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='无权限访问该社区'
            )

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message="验证通过"
        )

    def _execute(self, community_id: int, user_id: int, limit: int = 3) -> UseCaseResult:
        """
        执行获取未处理事件列表操作

        Args:
            community_id: 社区ID
            user_id: 用户ID
            limit: 最大返回数量（默认3）

        Returns:
            UseCaseResult: 执行结果
        """
        # 获取未处理事件
        events = CommunityDashboardService.get_pending_events(community_id, limit)

        current_app.logger.info(
            f'获取未处理事件成功: community_id={community_id}, count={events["total"]}'
        )
        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message='获取未处理事件成功',
            data=events
        )