"""
社区数字看板路由模块
处理社区数据看板相关的HTTP请求
"""
import logging
from flask import request, current_app
from . import community_dashboard_bp
from app.shared import make_succ_response, make_err_response
from app.shared.decorators import login_required
from wxcloudrun.community_dashboard_service import CommunityDashboardService

logger = logging.getLogger('CommunityDashboardRoutes')


@community_dashboard_bp.route('/community-dashboard/<int:community_id>/stats', methods=['GET'])
@login_required
def get_community_stats(decoded, community_id):
    """
    获取社区统计数据

    Args:
        decoded: 解码后的用户信息
        community_id: 社区ID

    Returns:
        统计数据响应
    """
    current_app.logger.info(f'=== 开始获取社区统计数据: {community_id} ===')

    user_id = decoded.get('user_id')

    try:
        # 检查权限
        if not CommunityDashboardService.has_permission(user_id, community_id):
            return make_err_response({}, '无权限访问该社区')

        # 获取统计数据
        stats = CommunityDashboardService.get_community_stats(community_id)

        current_app.logger.info(f'获取社区统计数据成功: community_id={community_id}')
        return make_succ_response(stats)

    except Exception as e:
        current_app.logger.error(f'获取社区统计数据失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取统计数据失败: {str(e)}')


@community_dashboard_bp.route('/community-dashboard/<int:community_id>/abnormal-users', methods=['GET'])
@login_required
def get_abnormal_users(decoded, community_id):
    """
    获取异常用户列表

    Args:
        decoded: 解码后的用户信息
        community_id: 社区ID

    Query Parameters:
        page: 页码（默认1）
        page_size: 每页数量（默认20，最大100）

    Returns:
        异常用户列表响应
    """
    current_app.logger.info(f'=== 开始获取异常用户列表: {community_id} ===')

    user_id = decoded.get('user_id')

    try:
        # 检查权限
        if not CommunityDashboardService.has_permission(user_id, community_id):
            return make_err_response({}, '无权限访问该社区')

        # 获取分页参数
        page = int(request.args.get('page', 1))
        page_size = min(int(request.args.get('page_size', 20)), 100)

        # 获取异常用户列表
        result = CommunityDashboardService.get_abnormal_users(
            community_id, page, page_size
        )

        current_app.logger.info(
            f'获取异常用户列表成功: community_id={community_id}, '
            f'count={len(result["users"])}, total={result["total"]}'
        )
        return make_succ_response(result)

    except Exception as e:
        current_app.logger.error(f'获取异常用户列表失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取异常用户列表失败: {str(e)}')


@community_dashboard_bp.route('/community-dashboard/<int:community_id>/trends', methods=['GET'])
@login_required
def get_trend_data(decoded, community_id):
    """
    获取历史趋势数据

    Args:
        decoded: 解码后的用户信息
        community_id: 社区ID

    Query Parameters:
        days: 天数（7或30，默认7）

    Returns:
        趋势数据响应
    """
    current_app.logger.info(f'=== 开始获取历史趋势数据: {community_id} ===')

    user_id = decoded.get('user_id')

    try:
        # 检查权限
        if not CommunityDashboardService.has_permission(user_id, community_id):
            return make_err_response({}, '无权限访问该社区')

        # 获取天数参数
        days = int(request.args.get('days', 7))
        if days not in [7, 30]:
            return make_err_response({}, '天数参数只能是 7 或 30')

        # 获取趋势数据
        trends = CommunityDashboardService.get_trend_data(community_id, days)

        current_app.logger.info(f'获取历史趋势数据成功: community_id={community_id}, days={days}')
        return make_succ_response(trends)

    except Exception as e:
        current_app.logger.error(f'获取历史趋势数据失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取趋势数据失败: {str(e)}')


@community_dashboard_bp.route('/community-dashboard/<int:community_id>/pending-events', methods=['GET'])
@login_required
def get_pending_events(decoded, community_id):
    """
    获取未处理事件列表

    Args:
        decoded: 解码后的用户信息
        community_id: 社区ID

    Query Parameters:
        limit: 最大返回数量（默认3）

    Returns:
        未处理事件列表响应
    """
    current_app.logger.info(f'=== 开始获取未处理事件: {community_id} ===')

    user_id = decoded.get('user_id')

    try:
        # 检查权限
        if not CommunityDashboardService.has_permission(user_id, community_id):
            return make_err_response({}, '无权限访问该社区')

        # 获取数量限制参数
        limit = int(request.args.get('limit', 3))

        # 获取未处理事件
        events = CommunityDashboardService.get_pending_events(community_id, limit)

        current_app.logger.info(
            f'获取未处理事件成功: community_id={community_id}, count={events["total"]}'
        )
        return make_succ_response(events)

    except Exception as e:
        current_app.logger.error(f'获取未处理事件失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取未处理事件失败: {str(e)}')


@community_dashboard_bp.route('/community-dashboard/<int:community_id>/user-abnormality/<int:user_id>', methods=['GET'])
@login_required
def get_user_abnormality_detail(decoded, community_id, user_id):
    """
    获取用户异常值详情

    Args:
        decoded: 解码后的用户信息
        community_id: 社区ID
        user_id: 用户ID

    Returns:
        用户异常值详情响应
    """
    current_app.logger.info(f'=== 开始获取用户异常值详情: community_id={community_id}, user_id={user_id} ===')

    try:
        # 检查权限
        if not CommunityDashboardService.has_permission(decoded.get('user_id'), community_id):
            return make_err_response({}, '无权限访问该社区')

        # 获取用户异常值详情
        detail = CommunityDashboardService.get_user_abnormality_detail(community_id, user_id)

        current_app.logger.info(f'获取用户异常值详情成功: user_id={user_id}')
        return make_succ_response(detail)

    except Exception as e:
        current_app.logger.error(f'获取用户异常值详情失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取异常值详情失败: {str(e)}')
