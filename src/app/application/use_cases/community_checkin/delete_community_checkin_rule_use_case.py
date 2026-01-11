"""
删除社区打卡规则用例
"""
from flask import current_app
from wxcloudrun.community_checkin_rule_service import CommunityCheckinRuleService


class DeleteCommunityCheckinRuleUseCase:
    """删除社区打卡规则用例"""

    def execute(self, rule_id: int, user_id: int) -> dict:
        """
        执行删除社区打卡规则操作

        Args:
            rule_id: 规则ID
            user_id: 用户ID

        Returns:
            dict: 包含成功状态和响应数据
        """
        try:
            # 调用服务层删除规则
            success = CommunityCheckinRuleService.delete_community_rule(
                rule_id, user_id
            )

            if success:
                current_app.logger.info(f'成功删除社区打卡规则，规则ID: {rule_id}')
                return {
                    'success': True,
                    'message': '删除成功',
                    'data': {
                        'rule_id': rule_id,
                        'message': '删除成功'
                    }
                }
            else:
                return {
                    'success': False,
                    'message': '删除失败',
                    'data': {}
                }

        except Exception as e:
            current_app.logger.error(f'删除社区打卡规则失败: {str(e)}', exc_info=True)
            return {
                'success': False,
                'message': f'删除规则失败: {str(e)}',
                'data': {}
            }