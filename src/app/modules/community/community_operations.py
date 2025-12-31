"""
社区操作路由
包含社区的创建、更新、状态切换和删除操作
"""

import logging
from flask import request, current_app
from . import community_bp
from app.shared import make_succ_response, make_err_response
from app.shared.utils.auth import verify_token
from database.flask_models import db, User, Community
from wxcloudrun.community_service import CommunityService
from wxcloudrun.utils.validators import _audit

app_logger = logging.getLogger('log')


@community_bp.route('/community/create', methods=['POST'])
def create_community():
    """创建社区"""
    current_app.logger.info('=== 开始创建社区 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    user = db.session.get(User, user_id)

    # 检查权限
    if not user or user.role < 3:  # 社区管理员及以上
        return make_err_response({}, '无权限创建社区')

    try:
        params = request.get_json()
        if not params:
            return make_err_response({}, '缺少请求参数')

        name = params.get('name', '').strip()
        description = params.get('description', '').strip()
        location = params.get('location', '').strip()
        location_lat = params.get('location_lat')
        location_lon = params.get('location_lon')
        manager_id = params.get('manager_id')

        if not name:
            return make_err_response({}, '社区名称不能为空')

        # 创建社区
        community = CommunityService.create_community(
            name=name,
            description=description,
            creator_id=user_id,
            location=location,
            location_lat=location_lat,
            location_lon=location_lon,
            manager_id=manager_id
        )

        # 获取主管信息
        manager = None
        if community.manager_id:
            manager_user = db.session.get(User, community.manager_id)
            if manager_user:
                manager = {
                    'user_id': manager_user.user_id,
                    'nickname': manager_user.nickname,
                    'avatar_url': manager_user.avatar_url
                }

        # 记录审计日志
        _audit(user_id, 'create_community', {
            'community_id': community.community_id,
            'name': name,
            'manager_id': manager_id
        })

        current_app.logger.info(f'创建社区成功: community_id={community.community_id}, name={name}, manager_id={manager_id}')
        return make_succ_response({
            'community_id': community.community_id,
            'name': community.name,
            'description': community.description,
            'creator_id': community.creator_id,
            'manager_id': community.manager_id,
            'manager_name': manager['nickname'] if manager else None,
            'manager': manager,
            'location': community.location,
            'location_lat': community.location_lat,
            'location_lon': community.location_lon,
            'status': community.status,
            'created_at': community.created_at.isoformat() if community.created_at else None,
            'message': '创建成功'
        })

    except Exception as e:
        current_app.logger.error(f'创建社区失败: {str(e)}', exc_info=True)
        return make_err_response({}, '创建失败')


@community_bp.route('/community/update', methods=['POST'])
def update_community():
    """更新社区信息"""
    current_app.logger.info('=== 开始更新社区信息 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    current_app.logger.info(f'操作用户ID: {user_id}')

    try:
        params = request.get_json()
        if not params:
            return make_err_response({}, '缺少请求参数')

        community_id = params.get('community_id')
        if not community_id:
            return make_err_response({}, '缺少社区ID')

        # 检查权限
        if not CommunityService.has_community_permission(user_id, community_id):
            return make_err_response({}, '无权限访问该社区')

        # 更新社区信息
        success = CommunityService.update_community(community_id, params, user_id)

        if success:
            # 记录审计日志
            _audit(user_id, 'update_community', {
                'community_id': community_id,
                'updated_fields': list(params.keys())
            })

            current_app.logger.info(f'更新社区信息成功: community_id={community_id}')
            return make_succ_response({'message': '更新成功'})
        else:
            return make_err_response({}, '更新失败')

    except Exception as e:
        current_app.logger.error(f'更新社区信息失败: {str(e)}', exc_info=True)
        return make_err_response({}, '更新失败')


@community_bp.route('/community/toggle-status', methods=['POST'])
def toggle_community_status():
    """切换社区状态"""
    current_app.logger.info('=== 开始切换社区状态 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    user = db.session.get(User, user_id)

    # 检查权限
    if not user or user.role == 1:  # 只有超级管理员可以切换状态
        return make_err_response({}, '无权限执行此操作')

    try:
        params = request.get_json()
        if not params:
            return make_err_response({}, '缺少请求参数')

        community_id = params.get('community_id')
        if not community_id:
            return make_err_response({}, '缺少社区ID')

        status = params.get('status')
        if not status:
            return make_err_response({}, '缺少状态参数')

        # 切换状态
        result = CommunityService.toggle_community_status(community_id, status)

        if result:
            # 记录审计日志
            _audit(user_id, 'toggle_community_status', {
                'community_id': community_id
            })

            current_app.logger.info(f'切换社区状态成功: community_id={community_id}')
            return make_succ_response({'message': '切换成功'})
        else:
            return make_err_response({}, '切换失败')

    except Exception as e:
        current_app.logger.error(f'切换社区状态失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'切换失败: {str(e)}')


@community_bp.route('/community/delete', methods=['POST'])
def delete_community():
    """删除社区"""
    current_app.logger.info('=== 开始删除社区 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    user = db.session.get(User, user_id)

    # 检查权限
    if not user or user.role < 4:  # 只有超级管理员可以删除社区
        return make_err_response({}, '无权限执行此操作')

    try:
        params = request.get_json()
        if not params:
            return make_err_response({}, '缺少请求参数')

        community_id = params.get('community_id')
        if not community_id:
            return make_err_response({}, '缺少社区ID')

        # 删除社区
        CommunityService.delete_community(community_id)

        # 获取社区信息用于返回
        community = db.session.get(Community, community_id)

        # 记录审计日志
        _audit(user_id, 'delete_community', {
            'community_id': community_id
        })

        current_app.logger.info(f'删除社区成功: community_id={community_id}')
        return make_succ_response({
            'community_id': community_id,
            'community_name': community.name if community else ''
        })
    except ValueError as e:
        # 检查是否是"社区还有用户"的错误
        if isinstance(e.args[0], dict) and 'user_count' in e.args[0]:
            user_count = e.args[0]['user_count']
            return make_err_response({
                'user_count': user_count
            }, '社区内还有用户，无法删除')
        else:
            return make_err_response({}, str(e))
    except Exception as e:
        current_app.logger.error(f'删除社区失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'删除失败: {str(e)}')