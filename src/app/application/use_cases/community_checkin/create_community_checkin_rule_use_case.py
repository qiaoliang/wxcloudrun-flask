"""
创建社区打卡规则用例
"""
from flask import current_app
from wxcloudrun.community_checkin_rule_service import CommunityCheckinRuleService


class CreateCommunityCheckinRuleUseCase:
    """创建社区打卡规则用例"""

    def execute(self, params: dict, community_id: int, user_id: int) -> dict:
        """
        执行创建社区打卡规则操作

        Args:
            params: 请求参数
            community_id: 社区ID
            user_id: 用户ID

        Returns:
            dict: 包含成功状态和响应数据
        """
        try:
            # 验证必要参数
            required_fields = ['rule_name']
            for field in required_fields:
                if field not in params:
                    return {
                        'success': False,
                        'message': f'缺少必要参数: {field}',
                        'data': {}
                    }

            # 调用服务层创建规则
            rule = CommunityCheckinRuleService.create_community_rule(
                params, community_id, user_id
            )

            current_app.logger.info(f'成功创建社区打卡规则，规则ID: {rule.community_rule_id}')
            return {
                'success': True,
                'message': '创建成功',
                'data': {
                    'rule_id': rule.community_rule_id,
                    'message': '创建成功'
                }
            }

        except Exception as e:
            current_app.logger.error(f'创建社区打卡规则失败: {str(e)}', exc_info=True)
            return {
                'success': False,
                'message': f'创建规则失败: {str(e)}',
                'data': {}
            }