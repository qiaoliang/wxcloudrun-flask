"""
获取历史趋势数据用例
"""
from flask import current_app
from wxcloudrun.community_dashboard_service import CommunityDashboardService


class GetTrendDataUseCase:
    """获取历史趋势数据用例"""

    def execute(self, community_id: int, user_id: int, days: int = 7) -> dict:
        """
        执行获取历史趋势数据操作

        Args:
            community_id: 社区ID
            user_id: 用户ID
            days: 天数（7或30，默认7）

        Returns:
            dict: 包含成功状态和响应数据
        """
        try:
            # 检查权限
            if not CommunityDashboardService.has_permission(user_id, community_id):
                return {
                    'success': False,
                    'message': '无权限访问该社区',
                    'data': {}
                }

            # 验证天数参数
            if days not in [7, 30]:
                return {
                    'success': False,
                    'message': '天数参数只能是 7 或 30',
                    'data': {}
                }

            # 获取趋势数据
            trends = CommunityDashboardService.get_trend_data(community_id, days)

            current_app.logger.info(f'获取历史趋势数据成功: community_id={community_id}, days={days}')
            return {
                'success': True,
                'message': '获取趋势数据成功',
                'data': trends
            }

        except Exception as e:
            current_app.logger.error(f'获取历史趋势数据失败: {str(e)}', exc_info=True)
            return {
                'success': False,
                'message': f'获取趋势数据失败: {str(e)}',
                'data': {}
            }