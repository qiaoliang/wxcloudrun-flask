"""
获取历史趋势数据用例
"""
from flask import current_app
from wxcloudrun.community_dashboard_service import CommunityDashboardService
from app.application.use_cases.base import BaseUseCase, UseCaseResult, UseCaseStatus


class GetTrendDataUseCase(BaseUseCase):
    """获取历史趋势数据用例"""

    def _validate(self, community_id: int, user_id: int, days: int = 7) -> UseCaseResult:
        """
        验证输入参数

        Args:
            community_id: 社区ID
            user_id: 用户ID
            days: 天数（7或30，默认7）

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

        # 验证天数参数
        if days not in [7, 30]:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='天数参数只能是 7 或 30'
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

    def _execute(self, community_id: int, user_id: int, days: int = 7) -> UseCaseResult:
        """
        执行获取历史趋势数据操作

        Args:
            community_id: 社区ID
            user_id: 用户ID
            days: 天数（7或30，默认7）

        Returns:
            UseCaseResult: 执行结果
        """
        # 获取趋势数据
        trends = CommunityDashboardService.get_trend_data(community_id, days)

        current_app.logger.info(f'获取历史趋势数据成功: community_id={community_id}, days={days}')
        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message='获取趋势数据成功',
            data=trends
        )