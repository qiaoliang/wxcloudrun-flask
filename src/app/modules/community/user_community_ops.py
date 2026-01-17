"""
用户社区操作路由
包含用户与社区相关的操作
"""

import logging
from flask import request, current_app
from . import community_bp
from app.shared import make_succ_response, make_err_response
from app.shared.utils.auth import verify_token
# 移除 db 直接访问,改用 UseCase
from wxcloudrun.utils.validators import _audit
from app.application.use_cases.community import (
    FormatCommunityInfoUseCase,
    GetUserWithCommunityUseCase,
    UpdateUserCommunityUseCase,
    CreateUserInCommunityUseCase,
    CheckCommunityPermissionUseCase
)

app_logger = logging.getLogger('log')


@community_bp.route('/user/community', methods=['GET'])
def get_user_community():
    """获取用户当前社区信息"""
    current_app.logger.info('=== 开始获取用户当前社区信息 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    current_app.logger.info(f'用户ID: {user_id}')

    try:
        # ✅ 使用 GetUserWithCommunityUseCase 获取用户和社区信息
        use_case = GetUserWithCommunityUseCase()
        result = use_case.execute(user_id)

        if not result.is_success:
            return make_err_response({}, result.message)

        current_app.logger.info(f'获取用户社区信息成功: user_id={user_id}')
        return make_succ_response(result.data)

    except Exception as e:
        current_app.logger.error(f'获取用户社区信息失败: {str(e)}', exc_info=True)
        return make_err_response({}, '获取社区信息失败')


@community_bp.route('/user/switch-community', methods=['POST'])
def switch_user_community():
    """切换用户社区"""
    current_app.logger.info('=== 开始切换用户社区 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    current_app.logger.info(f'用户ID: {user_id}')

    try:
        params = request.get_json()
        if not params:
            return make_err_response({}, '缺少请求参数')

        community_id = params.get('community_id')
        if not community_id:
            return make_err_response({}, '缺少社区ID')

        # ✅ 使用 UpdateUserCommunityUseCase 切换社区
        use_case = UpdateUserCommunityUseCase()
        result = use_case.execute(user_id, community_id)

        if not result.is_success:
            return make_err_response({}, result.message)

        # 记录审计日志
        _audit(user_id, 'switch_community', {
            'community_id': community_id
        })

        current_app.logger.info(f'切换用户社区成功: user_id={user_id}, community_id={community_id}')
        return make_succ_response(result.data)

    except Exception as e:
        current_app.logger.error(f'切换用户社区失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'切换失败: {str(e)}')


@community_bp.route('/community/create-user', methods=['POST'])
def create_community_user():
    """在社区中创建用户"""
    current_app.logger.info('=== 开始在社区中创建用户 ===')

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
        user_data = params.get('user_data', {})

        if not community_id or not user_data:
            return make_err_response({}, '缺少社区ID或用户数据')

        # 检查权限
        from app.application.use_cases.community import CheckCommunityPermissionUseCase
        check_permission_use_case = CheckCommunityPermissionUseCase()
        permission_result = check_permission_use_case.execute(operator_id, community_id)
        has_permission = permission_result.data.get('has_permission', False) if permission_result.is_success else False
        if not has_permission:
            return make_err_response({}, '无权限访问该社区')

        # ✅ 使用 CreateUserInCommunityUseCase 创建用户
        use_case = CreateUserInCommunityUseCase()
        result = use_case.execute(
            operator_id=operator_id,
            community_id=community_id,
            user_data=user_data
        )

        if not result.is_success:
            return make_err_response({}, result.message)

        # 记录审计日志
        created_user_id = result.data.get('user_id')
        _audit(operator_id, 'create_community_user', {
            'community_id': community_id,
            'created_user_id': created_user_id
        })

        current_app.logger.info(f'在社区中创建用户成功: community_id={community_id}, user_id={created_user_id}')
        return make_succ_response(result.data)
    except Exception as e:
        current_app.logger.error(f'在社区中创建用户失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'创建用户失败: {str(e)}')