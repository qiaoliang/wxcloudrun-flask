"""
批量获取规则来源信息用例
"""
from flask import current_app
from wxcloudrun.user_checkin_rule_service import UserCheckinRuleService


class GetRulesSourceInfoUseCase:
    """批量获取规则来源信息用例"""

    def execute(self, user_id: int, rule_ids: list = None,
                community_rule_ids: list = None) -> dict:
        """
        执行批量获取规则来源信息操作

        Args:
            user_id: 用户ID
            rule_ids: 个人规则ID列表
            community_rule_ids: 社区规则ID列表

        Returns:
            dict: 包含成功状态和响应数据
        """
        try:
            if rule_ids is None:
                rule_ids = []
            if community_rule_ids is None:
                community_rule_ids = []

            # 调用服务层获取规则来源信息
            source_info = UserCheckinRuleService.get_rules_source_info(
                user_id, rule_ids, community_rule_ids
            )

            current_app.logger.info(f'成功获取用户 {user_id} 的规则来源信息')
            return {
                'success': True,
                'message': '获取来源信息成功',
                'data': source_info
            }

        except Exception as e:
            current_app.logger.error(f'批量获取规则来源信息失败: {str(e)}', exc_info=True)
            return {
                'success': False,
                'message': f'获取来源信息失败: {str(e)}',
                'data': {}
            }