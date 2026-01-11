"""
获取用户今日打卡计划用例
"""
from flask import current_app
from wxcloudrun.user_checkin_rule_service import UserCheckinRuleService


class GetUserTodayPlanUseCase:
    """获取用户今日打卡计划用例"""

    def execute(self, user_id: int) -> dict:
        """
        执行获取用户今日打卡计划操作

        Args:
            user_id: 用户ID

        Returns:
            dict: 包含成功状态和响应数据
        """
        try:
            # 调用服务层获取今日打卡计划
            plan = UserCheckinRuleService.get_today_checkin_plan(user_id)

            current_app.logger.info(f'成功获取用户 {user_id} 的今日打卡计划，共 {plan.get("total_items", 0)} 项')
            return {
                'success': True,
                'message': '获取今日计划成功',
                'data': plan
            }

        except Exception as e:
            current_app.logger.error(f'获取用户今日打卡计划失败: {str(e)}', exc_info=True)
            return {
                'success': False,
                'message': f'获取今日计划失败: {str(e)}',
                'data': {}
            }