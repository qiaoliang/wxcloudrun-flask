"""
启用社区打卡规则用例
"""
from flask import current_app
from wxcloudrun.community_checkin_rule_service import CommunityCheckinRuleService


class EnableCommunityCheckinRuleUseCase:
    """启用社区打卡规则用例"""

    def execute(self, rule_id: int, user_id: int) -> dict:
        """
        执行启用社区打卡规则操作

        Args:
            rule_id: 规则ID
            user_id: 用户ID

        Returns:
            dict: 包含成功状态和响应数据
        """
        try:
            # 调用服务层启用规则
            rule = CommunityCheckinRuleService.enable_community_rule(
                rule_id, user_id
            )

            current_app.logger.info(f'成功启用社区打卡规则，规则ID: {rule.get("community_rule_id")}')
            return {
                'success': True,
                'message': '启用成功',
                'data': {
                    'rule_id': rule.get('community_rule_id'),
                    'message': '启用成功'
                }
            }

        except Exception as e:
            current_app.logger.error(f'启用社区打卡规则失败: {str(e)}', exc_info=True)
            return {
                'success': False,
                'message': f'启用规则失败: {str(e)}',
                'data': {}
            }