"""
获取社区打卡统计信息用例
"""
from flask import current_app
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from ..base import BaseUseCase, UseCaseResult, UseCaseStatus


class GetCommunityCheckinStatsUseCase(BaseUseCase):
    """获取社区打卡统计信息用例"""

    def __init__(self):
        """初始化用例，注入依赖的仓储"""
        self.dashboard_repository = RepositoryFactory.get_community_dashboard_repository()

    def _validate(self, community_id: int, user_id: int, days: int = 7) -> UseCaseResult:
        """
        验证参数

        Args:
            community_id: 社区ID
            user_id: 用户ID
            days: 统计天数（默认7天）

        Returns:
            UseCaseResult: 验证结果
        """
        if not isinstance(community_id, int) or community_id <= 0:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='社区ID必须为正整数'
            )

        if not isinstance(user_id, int) or user_id <= 0:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='用户ID必须为正整数'
            )

        if not isinstance(days, int) or days <= 0 or days > 365:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='统计天数必须在1-365之间'
            )

        # 检查权限
        if not self.dashboard_repository.has_permission(user_id, community_id):
            return UseCaseResult(
                status=UseCaseStatus.FORBIDDEN,
                message='无权限访问该社区'
            )

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message='验证通过'
        )

    def _execute(self, community_id: int, user_id: int, days: int = 7) -> UseCaseResult:
        """
        执行获取社区打卡统计信息操作

        Args:
            community_id: 社区ID
            user_id: 用户ID
            days: 统计天数（默认7天）

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 获取统计数据
            stats = self.dashboard_repository.get_community_checkin_stats(community_id, days)

            current_app.logger.info(
                f'成功获取社区 {community_id} 的打卡统计信息，共 {stats["total_rules"]} 个规则'
            )
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='获取统计信息成功',
                data=stats
            )

        except Exception as e:
            current_app.logger.error(f'获取社区打卡统计信息失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'获取统计信息失败: {str(e)}'
            )