"""
获取异常用户列表用例
"""
from flask import current_app
from wxcloudrun.community_dashboard_service import CommunityDashboardService


class GetAbnormalUsersUseCase:
    """获取异常用户列表用例"""

    def execute(self, community_id: int, user_id: int, page: int = 1,
                page_size: int = 20) -> dict:
        """
        执行获取异常用户列表操作

        Args:
            community_id: 社区ID
            user_id: 用户ID
            page: 页码（默认1）
            page_size: 每页数量（默认20，最大100）

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

            # 获取异常用户列表
            result = CommunityDashboardService.get_abnormal_users(
                community_id, page, page_size
            )

            current_app.logger.info(
                f'获取异常用户列表成功: community_id={community_id}, '
                f'count={len(result["users"])}, total={result["total"]}'
            )
            return {
                'success': True,
                'message': '获取异常用户列表成功',
                'data': result
            }

        except Exception as e:
            current_app.logger.error(f'获取异常用户列表失败: {str(e)}', exc_info=True)
            return {
                'success': False,
                'message': f'获取异常用户列表失败: {str(e)}',
                'data': {}
            }