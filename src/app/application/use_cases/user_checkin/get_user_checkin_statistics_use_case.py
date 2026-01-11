"""
获取用户打卡统计信息用例
"""
from flask import current_app
from wxcloudrun.user_checkin_rule_service import UserCheckinRuleService


class GetUserCheckinStatisticsUseCase:
    """获取用户打卡统计信息用例"""

    def execute(self, user_id: int, period: str = 'week',
                start_date: str = None, end_date: str = None) -> dict:
        """
        执行获取用户打卡统计信息操作

        Args:
            user_id: 用户ID
            period: 统计周期（week/month）
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            dict: 包含成功状态和响应数据
        """
        try:
            # 调用服务层获取统计信息
            stats = UserCheckinRuleService.get_user_checkin_statistics(
                user_id, period, start_date, end_date
            )

            current_app.logger.info(f'成功获取用户 {user_id} 的打卡统计信息')
            return {
                'success': True,
                'message': '获取统计信息成功',
                'data': stats
            }

        except Exception as e:
            current_app.logger.error(f'获取用户打卡统计信息失败: {str(e)}', exc_info=True)
            return {
                'success': False,
                'message': f'获取统计信息失败: {str(e)}',
                'data': {}
            }