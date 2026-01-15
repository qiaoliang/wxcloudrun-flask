"""
获取单个社区打卡规则详情用例
"""
from flask import current_app
from wxcloudrun.community_checkin_rule_service import CommunityCheckinRuleService
from ..base import BaseUseCase, UseCaseResult, UseCaseStatus


class GetCommunityCheckinRuleUseCase(BaseUseCase):
    """获取单个社区打卡规则详情用例"""

    def _validate(self, rule_id: int) -> UseCaseResult:
        """
        验证参数

        Args:
            rule_id: 规则ID

        Returns:
            UseCaseResult: 验证结果
        """
        if not isinstance(rule_id, int) or rule_id <= 0:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='规则ID必须为正整数'
            )

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message='验证通过'
        )

    def _execute(self, rule_id: int) -> UseCaseResult:
        """
        执行获取单个社区打卡规则详情操作

        Args:
            rule_id: 规则ID

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 调用服务层获取规则详情
            rule = CommunityCheckinRuleService.get_rule_detail(rule_id)

            current_app.logger.info(f'成功获取社区打卡规则详情，规则ID: {rule.get("community_rule_id")}')
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='获取规则详情成功',
                data={'rule': rule}
            )

        except Exception as e:
            current_app.logger.error(f'获取社区打卡规则详情失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'获取规则详情失败: {str(e)}'
            )