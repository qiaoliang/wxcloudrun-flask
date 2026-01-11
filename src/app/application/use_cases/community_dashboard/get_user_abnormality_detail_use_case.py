"""
获取用户异常值详情用例
"""
from flask import current_app
from wxcloudrun.community_dashboard_service import CommunityDashboardService


class GetUserAbnormalityDetailUseCase:
    """获取用户异常值详情用例"""

    def execute(self, community_id: int, user_id: int, request_user_id: int) -> dict:
        """
        执行获取用户异常值详情操作

        Args:
            community_id: 社区ID
            user_id: 用户ID（要查询的用户）
            request_user_id: 请求用户ID（用于权限检查）

        Returns:
            dict: 包含成功状态和响应数据
        """
        try:
            # 检查权限
            if not CommunityDashboardService.has_permission(request_user_id, community_id):
                return {
                    'success': False,
                    'message': '无权限访问该社区',
                    'data': {}
                }

            # 获取用户异常值详情
            detail = CommunityDashboardService.get_user_abnormality_detail(community_id, user_id)

            current_app.logger.info(f'获取用户异常值详情成功: user_id={user_id}')
            return {
                'success': True,
                'message': '获取异常值详情成功',
                'data': detail
            }

        except Exception as e:
            current_app.logger.error(f'获取用户异常值详情失败: {str(e)}', exc_info=True)
            return {
                'success': False,
                'message': f'获取异常值详情失败: {str(e)}',
                'data': {}
            }