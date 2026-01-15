"""
获取社区统计数据用例
"""
from flask import current_app
from wxcloudrun.community_dashboard_service import CommunityDashboardService
from app.application.use_cases.base import BaseUseCase, UseCaseResult, UseCaseStatus


class GetCommunityStatsUseCase(BaseUseCase):
    """获取社区统计数据用例"""

    def _validate(self, community_id: int, user_id: int) -> UseCaseResult:
        """
        验证输入参数

        Args:
            community_id: 社区ID
            user_id: 用户ID

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

    def _execute(self, community_id: int, user_id: int) -> UseCaseResult:
        """
        执行获取社区统计数据操作

        Args:
            community_id: 社区ID
            user_id: 用户ID

        Returns:
            UseCaseResult: 执行结果
        """
        # 获取统计数据
        stats = CommunityDashboardService.get_community_stats(community_id)

        current_app.logger.info(f'获取社区统计数据成功: community_id={community_id}')
        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message='获取统计数据成功',
            data=stats
        )