"""
获取用户所有打卡规则用例
"""
from flask import current_app
from wxcloudrun.user_checkin_rule_service import UserCheckinRuleService
from wxcloudrun.checkin_rule_service import CheckinRuleService


class GetUserAllRulesUseCase:
    """获取用户所有打卡规则用例"""

    def execute(self, user_id: int, method: str = 'GET', params: dict = None) -> dict:
        """
        执行获取用户所有打卡规则操作

        Args:
            user_id: 用户ID
            method: HTTP 方法（GET/DELETE）
            params: 请求参数（仅 DELETE 方法需要）

        Returns:
            dict: 包含成功状态和响应数据
        """
        try:
            # 处理 DELETE 方法（删除个人规则）
            if method == 'DELETE':
                if not params:
                    return {
                        'success': False,
                        'message': '缺少请求参数',
                        'data': {}
                    }

                rule_id = params.get('rule_id')
                rule_source = params.get('rule_source')

                if not rule_id:
                    return {
                        'success': False,
                        'message': '缺少规则ID参数',
                        'data': {}
                    }

                # 只允许删除个人规则
                if rule_source == 'community':
                    return {
                        'success': False,
                        'message': '不允许删除社区规则',
                        'data': {}
                    }

                # 调用 CheckinRuleService 删除个人规则
                response_data = CheckinRuleService.delete_rule(int(rule_id), user_id)
                current_app.logger.info(f'用户 {user_id} 成功删除个人打卡规则')
                return {
                    'success': True,
                    'message': '删除规则成功',
                    'data': response_data
                }

            # 处理 GET 方法（获取所有规则）
            # 调用服务层获取用户所有规则
            rules = UserCheckinRuleService.get_user_all_rules(user_id)

            current_app.logger.info(f'成功获取用户 {user_id} 的所有打卡规则，共 {len(rules)} 条规则')
            return {
                'success': True,
                'message': '获取规则成功',
                'data': rules
            }

        except Exception as e:
            current_app.logger.error(f'获取用户所有打卡规则失败: {str(e)}', exc_info=True)
            return {
                'success': False,
                'message': f'获取规则失败: {str(e)}',
                'data': {}
            }