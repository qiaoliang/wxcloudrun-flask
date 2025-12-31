"""
社区成员管理路由
包含社区成员的查询、添加和移除操作
"""

import logging
from flask import request, current_app
from . import community_bp
from app.shared import make_succ_response, make_err_response
from app.shared.utils.auth import verify_token
from wxcloudrun.community_service import CommunityService
from wxcloudrun.utils.validators import _audit

app_logger = logging.getLogger('log')


@community_bp.route('/communities/<int:community_id>/users', methods=['GET'])
def get_community_users(community_id):
    """获取社区用户列表"""
    current_app.logger.info(f'=== 开始获取社区用户列表: {community_id} ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    current_app.logger.info(f'请求用户ID: {user_id}')

    try:
        # 检查权限
        if not CommunityService.has_community_permission(user_id, community_id):
            return make_err_response({}, '无权限访问该社区')

        # 获取查询参数
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        role_filter = request.args.get('role')  # 可选的角色过滤

        # 获取社区用户
        members_data, total = CommunityService.get_community_members(
            community_id, page, per_page
        )

        # 格式化用户信息
        users_data = []
        for user in members_data:
            user_data = {
                'user_id': int(user['user_id']),
                'wechat_openid': '',  # get_community_members不返回此字段
                'phone_number': user.get('phone_number', ''),
                'nickname': user.get('nickname', ''),
                'name': user.get('nickname', ''),  # 使用nickname作为name
                'avatar_url': user.get('avatar_url', ''),
                'role': '普通用户',  # 固定值，因为这些是普通用户
                'status': 1,  # 固定值
                'created_at': user.get('join_time'),  # 使用join_time作为created_at
                'verification_status': 1  # 假设都已验证
            }
            users_data.append(user_data)

        response_data = {
            'users': users_data,
            'total': total,
            'page': page,
            'per_page': per_page,
            'has_next': len(users_data) == per_page
        }

        current_app.logger.info(f'获取社区用户列表成功: {community_id}, 共 {len(users_data)} 个用户')
        return make_succ_response(response_data)

    except Exception as e:
        current_app.logger.error(f'获取社区用户列表失败: {str(e)}', exc_info=True)
        return make_err_response({}, '获取社区用户列表失败')


@community_bp.route('/communities/<int:community_id>/users/<int:target_user_id>', methods=['DELETE'])
def remove_community_user(community_id, target_user_id):
    """从社区中移除用户"""
    current_app.logger.info(f'=== 开始移除社区用户: community_id={community_id}, user_id={target_user_id} ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    operator_id = decoded.get('user_id')
    current_app.logger.info(f'操作用户ID: {operator_id}')

    try:
        # 检查权限
        if not CommunityService.has_community_permission(operator_id, community_id):
            return make_err_response({}, '无权限访问该社区')

        # 移除用户
        result = CommunityService.remove_user_from_community(community_id, target_user_id)

        if result:
            # 记录审计日志
            _audit(operator_id, 'remove_community_user', {
                'community_id': community_id,
                'target_user_id': target_user_id
            })

            current_app.logger.info(f'移除社区用户成功: community_id={community_id}, user_id={target_user_id}, result={result}')
            return make_succ_response({'message': '移除成功', 'moved_to': result.get('moved_to')})
        else:
            return make_err_response({}, '移除失败')

    except Exception as e:
        current_app.logger.error(f'移除社区用户失败: {str(e)}', exc_info=True)
        return make_err_response({}, '移除失败')


@community_bp.route('/community/users', methods=['GET'])
def get_community_users_v2():
    """获取社区用户列表（新版）"""

    current_app.logger.info('=== 开始获取社区用户列表（新版） ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    current_app.logger.info(f'用户ID: {user_id}')

    try:
        # GET 请求从查询参数获取数据
        params = request.args.to_dict()
        community_id = params.get('community_id')

        if not community_id:
            return make_err_response({}, '缺少社区ID')

        # 检查权限
        if not CommunityService.has_community_permission(user_id, community_id):
            return make_err_response({}, '无权限访问该社区')

        # 获取社区用户
        users = CommunityService.get_community_users_v2(community_id)

        # 格式化用户信息
        users_data = []
        for user in users:
            user_info = {
                'user_id': user.user_id,
                'wechat_openid': user.wechat_openid,
                'phone_number': user.phone_number,
                'nickname': user.nickname,
                'name': user.name,
                'avatar_url': user.avatar_url,
                'role': user.role_name,
                'status': user.status,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'last_active_at': user.last_active_at.isoformat() if user.last_active_at else None
            }
            users_data.append(user_info)

        current_app.logger.info(f'获取社区用户列表成功: community_id={community_id}, 共 {len(users_data)} 个用户')
        return make_succ_response({'users': users_data})

    except Exception as e:
        current_app.logger.error(f'获取社区用户列表失败: {str(e)}', exc_info=True)
        return make_err_response({}, '获取用户列表失败')


@community_bp.route('/community/add-users', methods=['POST'])
def add_users_to_community():
    """批量添加用户到社区"""
    current_app.logger.info('=== 开始批量添加用户到社区 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    operator_id = decoded.get('user_id')
    current_app.logger.info(f'操作用户ID: {operator_id}')

    try:
        params = request.get_json()
        if not params:
            return make_err_response({}, '缺少请求参数')

        community_id = params.get('community_id')
        user_ids = params.get('user_ids', [])

        if not community_id or not user_ids:
            return make_err_response({}, '缺少社区ID或用户ID列表')

        # 检查权限
        if not CommunityService.has_community_permission(operator_id, community_id):
            return make_err_response({}, '无权限访问该社区')

        # 批量添加用户
        result = CommunityService.add_users_to_community(community_id, user_ids, operator_id)

        # 记录审计日志
        _audit(operator_id, 'add_users_to_community', {
            'community_id': community_id,
            'user_ids': user_ids,
            'success_count': result.get('success_count', 0),
            'fail_count': result.get('fail_count', 0)
        })

        current_app.logger.info(f'批量添加用户到社区完成: community_id={community_id}, 成功={result.get("success_count", 0)}, 失败={result.get("fail_count", 0)}')
        return make_succ_response(result)

    except Exception as e:
        current_app.logger.error(f'批量添加用户到社区失败: {str(e)}', exc_info=True)
        return make_err_response({}, '批量添加失败')


@community_bp.route('/community/remove-user', methods=['POST'])
def remove_user_from_community():
    """从社区中移除用户"""
    current_app.logger.info('=== 开始从社区中移除用户 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    operator_id = decoded.get('user_id')
    current_app.logger.info(f'操作用户ID: {operator_id}')

    try:
        params = request.get_json()
        if not params:
            return make_err_response({}, '缺少请求参数')

        community_id = params.get('community_id')
        target_user_id = params.get('user_id')

        if not all([community_id, target_user_id]):
            return make_err_response({}, '缺少社区ID或目标用户ID')

        # 检查权限
        if not CommunityService.has_community_permission(operator_id, community_id):
            return make_err_response({}, '无权限访问该社区')

        # 移除用户
        success = CommunityService.remove_user_from_community(community_id, target_user_id)

        if success:
            # 记录审计日志
            _audit(operator_id, 'remove_user_from_community', {
                'community_id': community_id,
                'target_user_id': target_user_id
            })

            current_app.logger.info(f'从社区中移除用户成功: community_id={community_id}, user_id={target_user_id}')
            return make_succ_response({'message': '移除成功'})
        else:
            return make_err_response({}, '移除失败')

    except Exception as e:
        current_app.logger.error(f'从社区中移除用户失败: {str(e)}', exc_info=True)
        return make_err_response({}, '移除失败')