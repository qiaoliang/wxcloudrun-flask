"""
获取用户打卡统计信息用例
"""
from flask import current_app
from wxcloudrun.user_checkin_rule_service import UserCheckinRuleService
from app.application.use_cases.base import BaseUseCase, UseCaseResult, UseCaseStatus


class GetUserCheckinStatisticsUseCase(BaseUseCase):
    """获取用户打卡统计信息用例"""

    def _validate(self, user_id: int, period: str = 'week',
                  start_date: str = None, end_date: str = None) -> UseCaseResult:
        """
        验证输入参数

        Args:
            user_id: 用户ID
            period: 统计周期（week/month）
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            UseCaseResult: 验证结果
        """
        if not user_id or user_id <= 0:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='用户ID无效'
            )

        if period not in ['week', 'month']:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='统计周期无效，必须是 week 或 month'
            )

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message="验证通过"
        )

    def _execute(self, user_id: int, period: str = 'week',
                 start_date: str = None, end_date: str = None) -> UseCaseResult:
        """
        执行获取用户打卡统计信息操作

        Args:
            user_id: 用户ID
            period: 统计周期（week/month）
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            UseCaseResult: 执行结果
        """
        # 调用服务层获取统计信息
        stats = UserCheckinRuleService.get_user_checkin_statistics(
            user_id, period, start_date, end_date
        )

        current_app.logger.info(f'成功获取用户 {user_id} 的打卡统计信息')
        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message='获取统计信息成功',
            data=stats
        )