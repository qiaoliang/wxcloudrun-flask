"""
更新社区打卡规则用例
"""
from flask import current_app
from wxcloudrun.community_checkin_rule_service import CommunityCheckinRuleService
from ..base import BaseUseCase, UseCaseResult, UseCaseStatus


class UpdateCommunityCheckinRuleUseCase(BaseUseCase):
    """更新社区打卡规则用例"""

    def _validate(self, rule_id: int, params: dict, user_id: int) -> UseCaseResult:
        """
        验证参数

        Args:
            rule_id: 规则ID
            params: 请求参数
            user_id: 用户ID

        Returns:
            UseCaseResult: 验证结果
        """
        if not isinstance(rule_id, int) or rule_id <= 0:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='规则ID必须为正整数'
            )

        if not params:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='请求参数不能为空'
            )

        if not isinstance(params, dict):
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='请求参数格式错误'
            )

        if not isinstance(user_id, int) or user_id <= 0:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='用户ID必须为正整数'
            )

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message='验证通过'
        )

    def _execute(self, rule_id: int, params: dict, user_id: int) -> UseCaseResult:
        """
        执行更新社区打卡规则操作

        Args:
            rule_id: 规则ID
            params: 请求参数
            user_id: 用户ID

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 调用服务层更新规则
            rule = CommunityCheckinRuleService.update_community_rule(
                rule_id, params, user_id
            )

            current_app.logger.info(f'成功更新社区打卡规则，规则ID: {rule.community_rule_id}')
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='更新成功',
                data={
                    'rule_id': rule.community_rule_id,
                    'message': '更新成功'
                }
            )

        except Exception as e:
            current_app.logger.error(f'更新社区打卡规则失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'更新规则失败: {str(e)}'
            )