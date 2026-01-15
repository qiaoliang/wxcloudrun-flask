"""
社区数字看板路由模块
处理社区数据看板相关的HTTP请求
"""
import logging
from flask import request, current_app
from . import community_dashboard_bp
from app.shared import make_succ_response, make_err_response
from app.shared.decorators import login_required
from app.application.use_cases.community_dashboard import (
    GetCommunityStatsUseCase,
    GetAbnormalUsersUseCase,
    GetTrendDataUseCase,
    GetPendingEventsUseCase,
    GetUserAbnormalityDetailUseCase
)

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
        use_case = GetCommunityStatsUseCase()
        result = use_case.execute(community_id, user_id)

        if result.is_success:
            return make_succ_response(result.data)
        else:
            return make_err_response(result.data, result.message)

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
        # 获取分页参数
        page = int(request.args.get('page', 1))
        page_size = min(int(request.args.get('page_size', 20)), 100)

        use_case = GetAbnormalUsersUseCase()
        result = use_case.execute(community_id, user_id, page, page_size)

        if result.is_success:
            return make_succ_response(result.data)
        else:
            return make_err_response(result.data, result.message)

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
        # 获取天数参数
        days = int(request.args.get('days', 7))

        use_case = GetTrendDataUseCase()
        result = use_case.execute(community_id, user_id, days)

        if result.is_success:
            return make_succ_response(result.data)
        else:
            return make_err_response(result.data, result.message)

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
        # 获取数量限制参数
        limit = int(request.args.get('limit', 3))

        use_case = GetPendingEventsUseCase()
        result = use_case.execute(community_id, user_id, limit)

        if result.is_success:
            return make_succ_response(result.data)
        else:
            return make_err_response(result.data, result.message)

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

    request_user_id = decoded.get('user_id')

    try:
        use_case = GetUserAbnormalityDetailUseCase()
        result = use_case.execute(community_id, user_id, request_user_id)

        if result.is_success:
            return make_succ_response(result.data)
        else:
            return make_err_response(result.data, result.message)

    except Exception as e:
        current_app.logger.error(f'获取用户异常值详情失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取异常值详情失败: {str(e)}')
