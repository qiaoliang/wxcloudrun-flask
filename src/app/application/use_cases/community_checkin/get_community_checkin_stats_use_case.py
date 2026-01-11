"""
获取社区打卡统计信息用例
"""
from flask import current_app
from wxcloudrun.community_service import CommunityService


class GetCommunityCheckinStatsUseCase:
    """获取社区打卡统计信息用例"""

    def execute(self, community_id: int, user_id: int, days: int = 7) -> dict:
        """
        执行获取社区打卡统计信息操作

        Args:
            community_id: 社区ID
            user_id: 用户ID
            days: 统计天数（默认7天）

        Returns:
            dict: 包含成功状态和响应数据
        """
        try:
            # 检查权限
            if not CommunityService.has_community_permission(user_id, community_id):
                return {
                    'success': False,
                    'message': '无权限访问该社区',
                    'data': {}
                }

            # 获取统计数据
            stats = CommunityService.get_community_checkin_stats(community_id, days)

            current_app.logger.info(
                f'成功获取社区 {community_id} 的打卡统计信息，共 {stats["total_rules"]} 个规则'
            )
            return {
                'success': True,
                'message': '获取统计信息成功',
                'data': stats
            }

        except Exception as e:
            current_app.logger.error(f'获取社区打卡统计信息失败: {str(e)}', exc_info=True)
            return {
                'success': False,
                'message': f'获取统计信息失败: {str(e)}',
                'data': {}
            }