"""
获取用户今日打卡计划用例
"""
from flask import current_app
from wxcloudrun.user_checkin_rule_service import UserCheckinRuleService
from app.application.use_cases.base import BaseUseCase, UseCaseResult, UseCaseStatus


class GetUserTodayPlanUseCase(BaseUseCase):
    """获取用户今日打卡计划用例"""

    def _validate(self, user_id: int) -> UseCaseResult:
        """
        验证输入参数

        Args:
            user_id: 用户ID

        Returns:
            UseCaseResult: 验证结果
        """
        if not user_id or user_id <= 0:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='用户ID无效'
            )

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message="验证通过"
        )

    def _execute(self, user_id: int) -> UseCaseResult:
        """
        执行获取用户今日打卡计划操作

        Args:
            user_id: 用户ID

        Returns:
            UseCaseResult: 执行结果
        """
        # 调用服务层获取今日打卡计划
        plan = UserCheckinRuleService.get_today_checkin_plan(user_id)

        current_app.logger.info(f'成功获取用户 {user_id} 的今日打卡计划，共 {plan.get("total_items", 0)} 项')
        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message='获取今日计划成功',
            data=plan
        )