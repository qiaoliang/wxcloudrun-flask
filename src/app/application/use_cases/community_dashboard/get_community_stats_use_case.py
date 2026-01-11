"""
获取社区统计数据用例
"""
from flask import current_app
from wxcloudrun.community_dashboard_service import CommunityDashboardService


class GetCommunityStatsUseCase:
    """获取社区统计数据用例"""

    def execute(self, community_id: int, user_id: int) -> dict:
        """
        执行获取社区统计数据操作

        Args:
            community_id: 社区ID
            user_id: 用户ID

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

            # 获取统计数据
            stats = CommunityDashboardService.get_community_stats(community_id)

            current_app.logger.info(f'获取社区统计数据成功: community_id={community_id}')
            return {
                'success': True,
                'message': '获取统计数据成功',
                'data': stats
            }

        except Exception as e:
            current_app.logger.error(f'获取社区统计数据失败: {str(e)}', exc_info=True)
            return {
                'success': False,
                'message': f'获取统计数据失败: {str(e)}',
                'data': {}
            }