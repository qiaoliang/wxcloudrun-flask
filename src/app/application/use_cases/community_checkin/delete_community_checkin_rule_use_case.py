"""
删除社区打卡规则用例
"""
from flask import current_app
from wxcloudrun.community_checkin_rule_service import CommunityCheckinRuleService
from ..base import BaseUseCase, UseCaseResult, UseCaseStatus


class DeleteCommunityCheckinRuleUseCase(BaseUseCase):
    """删除社区打卡规则用例"""

    def _validate(self, rule_id: int, user_id: int) -> UseCaseResult:
        """
        验证参数

        Args:
            rule_id: 规则ID
            user_id: 用户ID

        Returns:
            UseCaseResult: 验证结果
        """
        if not isinstance(rule_id, int) or rule_id <= 0:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='规则ID必须为正整数'
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

    def _execute(self, rule_id: int, user_id: int) -> UseCaseResult:
        """
        执行删除社区打卡规则操作

        Args:
            rule_id: 规则ID
            user_id: 用户ID

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 调用服务层删除规则
            success = CommunityCheckinRuleService.delete_community_rule(
                rule_id, user_id
            )

            if success:
                current_app.logger.info(f'成功删除社区打卡规则，规则ID: {rule_id}')
                return UseCaseResult(
                    status=UseCaseStatus.SUCCESS,
                    message='删除成功',
                    data={
                        'rule_id': rule_id,
                        'message': '删除成功'
                    }
                )
            else:
                return UseCaseResult(
                    status=UseCaseStatus.FAILURE,
                    message='删除失败'
                )

        except Exception as e:
            current_app.logger.error(f'删除社区打卡规则失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'删除规则失败: {str(e)}'
            )