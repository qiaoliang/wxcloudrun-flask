"""
更新社区打卡规则用例
"""
from flask import current_app
from wxcloudrun.community_checkin_rule_service import CommunityCheckinRuleService


class UpdateCommunityCheckinRuleUseCase:
    """更新社区打卡规则用例"""

    def execute(self, rule_id: int, params: dict, user_id: int) -> dict:
        """
        执行更新社区打卡规则操作

        Args:
            rule_id: 规则ID
            params: 请求参数
            user_id: 用户ID

        Returns:
            dict: 包含成功状态和响应数据
        """
        try:
            # 验证必要参数
            if not params:
                return {
                    'success': False,
                    'message': '缺少请求参数',
                    'data': {}
                }

            # 调用服务层更新规则
            rule = CommunityCheckinRuleService.update_community_rule(
                rule_id, params, user_id
            )

            current_app.logger.info(f'成功更新社区打卡规则，规则ID: {rule.community_rule_id}')
            return {
                'success': True,
                'message': '更新成功',
                'data': {
                    'rule_id': rule.community_rule_id,
                    'message': '更新成功'
                }
            }

        except Exception as e:
            current_app.logger.error(f'更新社区打卡规则失败: {str(e)}', exc_info=True)
            return {
                'success': False,
                'message': f'更新规则失败: {str(e)}',
                'data': {}
            }