"""
批量获取规则来源信息用例
"""
from flask import current_app
from wxcloudrun.user_checkin_rule_service import UserCheckinRuleService
from app.application.use_cases.base import BaseUseCase, UseCaseResult, UseCaseStatus


class GetRulesSourceInfoUseCase(BaseUseCase):
    """批量获取规则来源信息用例"""

    def _validate(self, user_id: int, rule_ids: list = None,
                  community_rule_ids: list = None) -> UseCaseResult:
        """
        验证输入参数

        Args:
            user_id: 用户ID
            rule_ids: 个人规则ID列表
            community_rule_ids: 社区规则ID列表

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

    def _execute(self, user_id: int, rule_ids: list = None,
                 community_rule_ids: list = None) -> UseCaseResult:
        """
        执行批量获取规则来源信息操作

        Args:
            user_id: 用户ID
            rule_ids: 个人规则ID列表
            community_rule_ids: 社区规则ID列表

        Returns:
            UseCaseResult: 执行结果
        """
        if rule_ids is None:
            rule_ids = []
        if community_rule_ids is None:
            community_rule_ids = []

        # 调用服务层获取规则来源信息
        source_info = UserCheckinRuleService.get_rules_source_info(
            user_id, rule_ids, community_rule_ids
        )

        current_app.logger.info(f'成功获取用户 {user_id} 的规则来源信息')
        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message='获取来源信息成功',
            data=source_info
        )