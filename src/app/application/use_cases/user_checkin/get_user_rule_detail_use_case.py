"""
获取用户打卡规则详情用例
"""
from flask import current_app
from wxcloudrun.user_checkin_rule_service import UserCheckinRuleService


class GetUserRuleDetailUseCase:
    """获取用户打卡规则详情用例"""

    def execute(self, user_id: int, rule_id: int) -> dict:
        """
        执行获取用户打卡规则详情操作

        Args:
            user_id: 用户ID
            rule_id: 规则ID

        Returns:
            dict: 包含成功状态和响应数据
        """
        try:
            # 调用服务层获取规则详情
            rule = UserCheckinRuleService.get_user_rule_detail(user_id, rule_id)

            current_app.logger.info(f'成功获取用户 {user_id} 的规则详情，规则ID: {rule_id}')
            return {
                'success': True,
                'message': '获取规则详情成功',
                'data': rule
            }

        except Exception as e:
            current_app.logger.error(f'获取用户打卡规则详情失败: {str(e)}', exc_info=True)
            return {
                'success': False,
                'message': f'获取规则详情失败: {str(e)}',
                'data': {}
            }