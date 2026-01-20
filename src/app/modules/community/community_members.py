"""
社区成员管理路由
包含社区成员的查询、添加和移除操作
"""

import logging
from flask import request, current_app
from . import community_bp
from app.shared import make_succ_response, make_err_response
from app.shared.utils.auth import verify_token
from wxcloudrun.utils.validators import _audit
from app.application.use_cases.community import (
    CheckCommunityPermissionUseCase,
    GetCommunityMembersUseCase,
    RemoveUserFromCommunityUseCase,
    AddUsersToCommunityUseCase,
    ListCommunityUsersUseCase
)

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
        check_permission_use_case = CheckCommunityPermissionUseCase()
        permission_result = check_permission_use_case.execute(user_id, community_id)
        has_permission = permission_result.data.get('has_permission', False) if permission_result.is_success else False
        if not has_permission:
            return make_err_response({}, '无权限访问该社区')

        # 获取查询参数
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        role_filter = request.args.get('role')  # 可选的角色过滤

        # 使用应用服务用例获取社区用户
        get_members_use_case = GetCommunityMembersUseCase()
        members_result = get_members_use_case.execute(community_id, page, per_page)

        if not members_result.is_success:
            return make_err_response({}, members_result.message)

        # 格式化用户信息
        users_data = []
        for user in members_result.data.get('members', []):
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
            'total': members_result.data.get('total', 0),
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
        check_permission_use_case = CheckCommunityPermissionUseCase()
        permission_result = check_permission_use_case.execute(operator_id, community_id)
        has_permission = permission_result.data.get('has_permission', False) if permission_result.is_success else False
        if not has_permission:
            return make_err_response({}, '无权限访问该社区')

        # 使用应用服务用例移除用户
        remove_user_use_case = RemoveUserFromCommunityUseCase()
        result = remove_user_use_case.execute(community_id, target_user_id)

        if result.is_success:
            # 记录审计日志
            _audit(operator_id, 'remove_community_user', {
                'community_id': community_id,
                'target_user_id': target_user_id
            })

            current_app.logger.info(f'移除社区用户成功: community_id={community_id}, user_id={target_user_id}')
            return make_succ_response({'message': '移除成功', 'moved_to': result.data.get('moved_to')})
        else:
            return make_err_response({}, result.message)

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
        check_permission_use_case = CheckCommunityPermissionUseCase()
        permission_result = check_permission_use_case.execute(user_id, int(community_id))
        has_permission = permission_result.data.get('has_permission', False) if permission_result.is_success else False
        if not has_permission:
            return make_err_response({}, '无权限访问该社区')

        # 使用应用服务用例获取社区用户

        use_case = ListCommunityUsersUseCase()
        result = use_case.execute(
            community_id=int(community_id),
            role=params.get('role'),
            keyword=params.get('keyword'),
            page=int(params.get('page', 1)),
            page_size=int(params.get('page_size', 20))
        )

        if not result.is_success:
            return make_err_response({}, result.message)

        current_app.logger.info(f'获取社区用户列表成功: community_id={community_id}, 共 {result.data["total"]} 个用户')
        return make_succ_response(result.data)

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
        check_permission_use_case = CheckCommunityPermissionUseCase()
        permission_result = check_permission_use_case.execute(operator_id, community_id)
        has_permission = permission_result.data.get('has_permission', False) if permission_result.is_success else False
        if not has_permission:
            return make_err_response({}, '无权限访问该社区')

        # 使用应用服务用例批量添加用户
        add_users_use_case = AddUsersToCommunityUseCase()
        result = add_users_use_case.execute(community_id, user_ids, operator_id)

        if not result.is_success:
            return make_err_response({}, result.message)

        # 记录审计日志
        _audit(operator_id, 'add_users_to_community', {
            'community_id': community_id,
            'user_ids': user_ids,
            'success_count': result.data.get('success_count', 0),
            'fail_count': result.data.get('fail_count', 0)
        })

        current_app.logger.info(f'批量添加用户到社区完成: community_id={community_id}, 成功={result.data.get("success_count", 0)}, 失败={result.data.get("fail_count", 0)}')
        return make_succ_response(result.data)

    except Exception as e:
        current_app.logger.error(f'批量添加用户到社区失败: {str(e)}', exc_info=True)
        return make_err_response({}, '批量添加失败')


@community_bp.route('/communities/<int:community_id>/users/<int:target_user_id>', methods=['DELETE'])
def remove_user_from_community_restful(community_id, target_user_id):
    """从社区中移除用户（RESTful API）- 重写自 POST /api/community/remove-user"""
    current_app.logger.info('=== 开始从社区中移除用户（RESTful） ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    operator_id = decoded.get('user_id')
    current_app.logger.info(f'操作用户ID: {operator_id}, 社区ID: {community_id}, 目标用户ID: {target_user_id}')

    try:
        # 检查权限
        check_permission_use_case = CheckCommunityPermissionUseCase()
        permission_result = check_permission_use_case.execute(operator_id, community_id)
        has_permission = permission_result.data.get('has_permission', False) if permission_result.is_success else False
        if not has_permission:
            return make_err_response({}, '无权限访问该社区')

        # 使用应用服务用例移除用户
        remove_user_use_case = RemoveUserFromCommunityUseCase()
        result = remove_user_use_case.execute(community_id, target_user_id)

        if result.is_success:
            # 记录审计日志
            _audit(operator_id, 'remove_user_from_community', {
                'community_id': community_id,
                'target_user_id': target_user_id
            })

            current_app.logger.info(f'从社区中移除用户成功: community_id={community_id}, user_id={target_user_id}')
            return make_succ_response({'message': '移除成功'})
        else:
            return make_err_response({}, result.message)

    except Exception as e:
        current_app.logger.error(f'从社区中移除用户失败: {str(e)}', exc_info=True)
        return make_err_response({}, '移除失败')


@community_bp.route('/community/remove-user', methods=['POST'])
def remove_user_from_community():
    """从社区中移除用户（已废弃）- 请使用 DELETE /api/communities/<id>/users/<user_id>"""
    current_app.logger.info('=== 开始从社区中移除用户（已废弃） ===')

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
        check_permission_use_case = CheckCommunityPermissionUseCase()
        permission_result = check_permission_use_case.execute(operator_id, community_id)
        has_permission = permission_result.data.get('has_permission', False) if permission_result.is_success else False
        if not has_permission:
            return make_err_response({}, '无权限访问该社区')

        # 使用应用服务用例移除用户
        remove_user_use_case = RemoveUserFromCommunityUseCase()
        result = remove_user_use_case.execute(community_id, target_user_id)

        if result.is_success:
            # 记录审计日志
            _audit(operator_id, 'remove_user_from_community', {
                'community_id': community_id,
                'target_user_id': target_user_id
            })

            current_app.logger.info(f'从社区中移除用户成功: community_id={community_id}, user_id={target_user_id}')

            # 添加 deprecation 警告
            response = make_succ_response({'message': '移除成功'})
            response.headers['Deprecation'] = 'Use DELETE /api/communities/<id>/users/<user_id> instead'
            response.headers['Warning'] = '299 - "Deprecated API: Use DELETE /api/communities/<id>/users/<user_id> instead"'

            return response
        else:
            return make_err_response({}, result.message)

    except Exception as e:
        current_app.logger.error(f'从社区中移除用户失败: {str(e)}', exc_info=True)
        return make_err_response({}, '移除失败')