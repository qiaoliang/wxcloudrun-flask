"""
创建社区打卡规则用例
"""
from flask import current_app
from wxcloudrun.community_checkin_rule_service import CommunityCheckinRuleService
from ..base import BaseUseCase, UseCaseResult, UseCaseStatus


class CreateCommunityCheckinRuleUseCase(BaseUseCase):
    """创建社区打卡规则用例"""

    def _validate(self, params: dict, community_id: int, user_id: int) -> UseCaseResult:
        """
        验证参数

        Args:
            params: 请求参数
            community_id: 社区ID
            user_id: 用户ID

        Returns:
            UseCaseResult: 验证结果
        """
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

        required_fields = ['rule_name']
        for field in required_fields:
            if field not in params:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message=f'缺少必要参数: {field}'
                )

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

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message='验证通过'
        )

    def _execute(self, params: dict, community_id: int, user_id: int) -> UseCaseResult:
        """
        执行创建社区打卡规则操作

        Args:
            params: 请求参数
            community_id: 社区ID
            user_id: 用户ID

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 调用服务层创建规则
            rule = CommunityCheckinRuleService.create_community_rule(
                params, community_id, user_id
            )

            current_app.logger.info(f'成功创建社区打卡规则，规则ID: {rule.community_rule_id}')
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='创建成功',
                data={
                    'rule_id': rule.community_rule_id,
                    'message': '创建成功'
                }
            )

        except Exception as e:
            current_app.logger.error(f'创建社区打卡规则失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'创建规则失败: {str(e)}'
            )