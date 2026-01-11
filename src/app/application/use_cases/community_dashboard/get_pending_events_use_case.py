"""
获取未处理事件列表用例
"""
from flask import current_app
from wxcloudrun.community_dashboard_service import CommunityDashboardService


class GetPendingEventsUseCase:
    """获取未处理事件列表用例"""

    def execute(self, community_id: int, user_id: int, limit: int = 3) -> dict:
        """
        执行获取未处理事件列表操作

        Args:
            community_id: 社区ID
            user_id: 用户ID
            limit: 最大返回数量（默认3）

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

            # 获取未处理事件
            events = CommunityDashboardService.get_pending_events(community_id, limit)

            current_app.logger.info(
                f'获取未处理事件成功: community_id={community_id}, count={events["total"]}'
            )
            return {
                'success': True,
                'message': '获取未处理事件成功',
                'data': events
            }

        except Exception as e:
            current_app.logger.error(f'获取未处理事件失败: {str(e)}', exc_info=True)
            return {
                'success': False,
                'message': f'获取未处理事件失败: {str(e)}',
                'data': {}
            }