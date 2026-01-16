"""
社区基础管理路由
包含社区列表、详情查询等基础功能
"""

import logging
from flask import request, current_app
from sqlalchemy import select
from . import community_bp
from app.shared import make_succ_response, make_err_response
from app.shared.utils.auth import verify_token, get_current_user
from database.flask_models import db, User, Community
from app.application.use_cases.community import (
    GetManagedCommunitiesUseCase,
    GetAvailableCommunitiesUseCase,
    SearchManageableCommunitiesUseCase,
    CheckCommunityPermissionUseCase
)
from .utils import _check_superadmin_permission, _format_community_info

app_logger = logging.getLogger('log')


def _format_community_info_from_dict(community_dict: dict) -> dict:
    """格式化社区信息（从字典）"""
    return {
        'community_id': community_dict.get('community_id'),
        'name': community_dict.get('name'),
        'description': community_dict.get('description'),
        'address': community_dict.get('address'),
        'contact_phone': community_dict.get('contact_phone'),
        'status': community_dict.get('status'),
        'created_at': community_dict.get('created_at')
    }


@community_bp.route('/communities', methods=['GET'])
def get_communities():
    """获取社区列表（超级管理员专用）- 为了兼容应用初始化测试"""
    current_app.logger.info('=== 开始获取社区列表 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    user = db.session.get(User, user_id)

    # 检查权限
    error = _check_superadmin_permission(user)
    if error:
        return error

    try:
        # 使用 SQLAlchemy 2.0 的 select() 语句
        # 查询所有社区
        stmt = select(Community)
        communities = db.session.execute(stmt).scalars().all()

        # 格式化社区信息
        communities_data = []
        for community in communities:
            community_data = _format_community_info(community, include_worker_stats=True)
            communities_data.append(community_data)

        current_app.logger.info(f'获取社区列表成功，共 {len(communities_data)} 个社区')
        return make_succ_response({'communities': communities_data})

    except Exception as e:
        current_app.logger.error(f'获取社区列表失败: {str(e)}', exc_info=True)
        return make_err_response({}, '获取社区列表失败')


@community_bp.route('/community/list', methods=['GET'])
def get_community_list():
    """获取社区列表（用户可见的社区列表）"""
    current_app.logger.info('=== 开始获取社区列表（用户可见） ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    current_app.logger.info(f'用户ID: {user_id}')

    try:
        # 使用UseCase获取用户可见的社区列表
        get_available_use_case = GetAvailableCommunitiesUseCase()
        result = get_available_use_case.execute(user_id=user_id)

        if not result.is_success:
            return make_err_response({}, result.message)

        # 格式化社区信息（包含主管信息）
        communities_data = []
        for community in result.data.get('communities', []):
            community_data = _format_community_info(community, include_worker_stats=True)
            communities_data.append(community_data)

        current_app.logger.info(f'获取用户社区列表成功，共 {len(communities_data)} 个社区')
        return make_succ_response({'communities': communities_data})

    except Exception as e:
        current_app.logger.error(f'获取用户社区列表失败: {str(e)}', exc_info=True)
        return make_err_response({}, '获取社区列表失败')


@community_bp.route('/communities/available', methods=['GET'])
def get_available_communities():
    """获取可加入的社区列表"""
    current_app.logger.info('=== 开始获取可加入社区列表 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    current_app.logger.info(f'用户ID: {user_id}')

    try:
        # 使用UseCase获取可加入的社区列表
        get_available_use_case = GetAvailableCommunitiesUseCase()
        result = get_available_use_case.execute(user_id=user_id)

        if not result.is_success:
            return make_err_response({}, result.message)

        # 格式化社区信息
        communities_data = []
        for community in result.data.get('communities', []):
            community_data = _format_community_info(community)
            communities_data.append(community_data)

        current_app.logger.info(f'获取可加入社区列表成功，共 {len(communities_data)} 个社区')
        return make_succ_response({'communities': communities_data})

    except Exception as e:
        current_app.logger.error(f'获取可加入社区列表失败: {str(e)}', exc_info=True)
        return make_err_response({}, '获取可加入社区列表失败')


@community_bp.route('/user/managed-communities', methods=['GET'])
def get_managed_communities():
    """获取用户管理的社区列表（默认7个）"""
    from app.shared.utils.auth import get_current_user

    current_app.logger.info('=== 开始获取可管理社区列表 ===')

    # 获取当前用户（装饰器已验证token）
    user = get_current_user()

    if not user:
        return make_err_response({}, '用户不存在')

    try:
        # 使用UseCase获取用户可管理的社区
        get_managed_use_case = GetManagedCommunitiesUseCase()
        result = get_managed_use_case.execute(user_id=user.user_id, limit=7)

        if not result.is_success:
            return make_err_response({}, result.message)

        # 格式化社区信息
        communities_data = []
        for community in result.data.get('communities', []):
            community_data = _format_community_info_from_dict(community)
            communities_data.append(community_data)

        current_app.logger.info(f'获取可管理社区列表成功，共 {len(communities_data)} 个社区')
        return make_succ_response({'communities': communities_data})

    except Exception as e:
        current_app.logger.error(f'获取可管理社区列表失败: {str(e)}', exc_info=True)
        return make_err_response({}, '获取可管理社区列表失败')


@community_bp.route('/community/communities/manage/list', methods=['GET'])
def get_manageable_communities():
    """获取可管理的社区列表"""
    current_app.logger.info('=== 开始获取可管理的社区列表 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    current_app.logger.info(f'用户ID: {user_id}')

    try:
        # 使用UseCase获取用户可管理的社区
        get_managed_use_case = GetManagedCommunitiesUseCase()
        result = get_managed_use_case.execute(user_id=user_id, limit=100)

        if not result.is_success:
            return make_err_response({}, result.message)

        # 格式化社区信息
        communities_data = []
        for community in result.data.get('communities', []):
            community_data = _format_community_info_from_dict(community)
            communities_data.append(community_data)

        current_app.logger.info(f'获取可管理社区列表成功，共 {len(communities_data)} 个社区')
        return make_succ_response({'communities': communities_data})

    except Exception as e:
        current_app.logger.error(f'获取可管理社区列表失败: {str(e)}', exc_info=True)
        return make_err_response({}, '获取可管理社区列表失败')


@community_bp.route('/communities/manage/search', methods=['GET'])
def search_manageable_communities():
    """搜索可管理的社区"""
    current_app.logger.info('=== 开始搜索可管理的社区 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    current_app.logger.info(f'用户ID: {user_id}')

    try:
        # 获取搜索参数
        keyword = request.args.get('keyword', '').strip()
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)

        # 使用UseCase执行搜索
        search_use_case = SearchManageableCommunitiesUseCase()
        result = search_use_case.execute(
            user_id=user_id,
            keyword=keyword,
            page=page,
            per_page=per_page
        )

        if not result.is_success:
            return make_err_response({}, result.message)

        current_app.logger.info(f'搜索结果: 找到 {result.data["total"]} 条记录')

        return make_succ_response(result.data)

    except Exception as e:
        current_app.logger.error(f'搜索可管理社区失败: {str(e)}', exc_info=True)
        return make_err_response({}, '搜索失败')


@community_bp.route('/communities/<int:community_id>', methods=['GET'])
def get_community_detail(community_id):
    """获取社区详情"""
    current_app.logger.info(f'=== 开始获取社区详情: {community_id} ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    current_app.logger.info(f'用户ID: {user_id}')

    try:
        # 检查权限
        check_permission_use_case = CheckCommunityPermissionUseCase()
        permission_result = check_permission_use_case.execute(user_id, community_id)
        has_permission = permission_result.data.get('has_permission', False) if permission_result.is_success else False

        if not has_permission:
            return make_err_response({}, '无权限访问该社区')

        # 使用应用服务用例获取社区详情
        from app.application.use_cases.community import GetCommunityDetailsUseCase

        use_case = GetCommunityDetailsUseCase()
        result = use_case.execute(community_id=community_id)

        if not result.is_success:
            return make_err_response({}, result.message)

        # 获取社区统计信息
        from app.application.use_cases.events import GetCommunityStatsUseCase

        stats_use_case = GetCommunityStatsUseCase()
        stats_result = stats_use_case.execute(community_id=community_id)

        # 构建响应数据结构
        response_data = {
            'community': result.data,
            'stats': {
                'staff_count': result.data.get('staff_count', 0),  # 专员数量
                'worker_count': result.data.get('staff_count', 0),  # 工作人员总数
                'user_count': result.data.get('user_count', 0),  # 普通成员数量（不包括工作人员）
                'manager_count': 1 if result.data.get('manager') else 0,  # 主管数量
                'support_count': stats_result.data.get('support_count', 0) if stats_result.is_success else 0,
                'active_events': stats_result.data.get('active_events', 0) if stats_result.is_success else 0,
                'checkin_rate': 0  # TODO: 计算打卡率
            }
        }

        current_app.logger.info(f'获取社区详情成功: community_id={community_id}')
        return make_succ_response(response_data)

    except Exception as e:
        current_app.logger.error(f'获取社区详情失败: {str(e)}', exc_info=True)
        return make_err_response({}, '获取社区详情失败')