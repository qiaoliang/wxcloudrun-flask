"""
获取用户打卡规则详情用例
"""
from flask import current_app
from wxcloudrun.user_checkin_rule_service import UserCheckinRuleService
from app.application.use_cases.base import BaseUseCase, UseCaseResult, UseCaseStatus


class GetUserRuleDetailUseCase(BaseUseCase):
    """获取用户打卡规则详情用例"""

    def _validate(self, user_id: int, rule_id: int) -> UseCaseResult:
        """
        验证输入参数

        Args:
            user_id: 用户ID
            rule_id: 规则ID

        Returns:
            UseCaseResult: 验证结果
        """
        if not user_id or user_id <= 0:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='用户ID无效'
            )

        if not rule_id or rule_id <= 0:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='规则ID无效'
            )

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message="验证通过"
        )

    def _execute(self, user_id: int, rule_id: int) -> UseCaseResult:
        """
        执行获取用户打卡规则详情操作

        Args:
            user_id: 用户ID
            rule_id: 规则ID

        Returns:
            UseCaseResult: 执行结果
        """
        # 调用服务层获取规则详情
        rule = UserCheckinRuleService.get_user_rule_detail(user_id, rule_id)

        current_app.logger.info(f'成功获取用户 {user_id} 的规则详情，规则ID: {rule_id}')
        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message='获取规则详情成功',
            data=rule
        )