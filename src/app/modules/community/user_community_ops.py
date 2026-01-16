"""
用户社区操作路由
包含用户与社区相关的操作
"""

import logging
from flask import request, current_app
from . import community_bp
from app.shared import make_succ_response, make_err_response
from app.shared.utils.auth import verify_token
from database.flask_models import db, User, Community
from wxcloudrun.utils.validators import _audit
from .utils import _format_community_info

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
        user = db.session.get(User, user_id)
        if not user:
            return make_err_response({}, '用户不存在')

        if not user.community_id:
            return make_err_response({}, '用户未加入社区')

        community = db.session.get(Community, user.community_id)
        if not community:
            return make_err_response({}, '社区不存在')

        # 检查用户是否真的属于该社区
        from app.application.use_cases.community import VerifyUserCommunityAccessUseCase
        verify_access_use_case = VerifyUserCommunityAccessUseCase()
        access_result = verify_access_use_case.execute(user_id, user.community_id)
        has_access = access_result.data.get('has_access', False) if access_result.is_success else False
        if not has_access:
            return make_err_response({}, '用户不属于该社区')

        community_data = _format_community_info(community)

        current_app.logger.info(f'获取用户社区信息成功: user_id={user_id}, community_id={user.community_id}')
        return make_succ_response(community_data)

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

        # 切换社区
        user = db.session.get(User, user_id)
        if not user:
            return make_err_response({}, '用户不存在')

        user.community_id = community_id
        db.session.commit()

        # 记录审计日志
        _audit(user_id, 'switch_community', {
            'community_id': community_id
        })

        current_app.logger.info(f'切换用户社区成功: user_id={user_id}, community_id={community_id}')
        return make_succ_response({'message': '切换成功'})

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

        # 创建用户
        # TODO: 需要实现 CreateUserInCommunityUseCase
        # 临时使用直接创建的方式
        user = User(
            phone_number=user_data.get('phone_number'),
            nickname=user_data.get('nickname', ''),
            name=user_data.get('name', ''),
            avatar_url=user_data.get('avatar_url', ''),
            role=user_data.get('role', 1),
            community_id=community_id
        )
        db.session.add(user)
        db.session.commit()
        if user:
            # 记录审计日志
            _audit(operator_id, 'create_community_user', {
                'community_id': community_id,
                'created_user_id': user.user_id
            })

            current_app.logger.info(f'在社区中创建用户成功: community_id={community_id}, user_id={user.user_id}')
            return make_succ_response({
                'user_id': user.user_id,
                'message': '创建成功'
            })
        else:
            return make_err_response({}, '创建失败')
    except Exception as e:
        current_app.logger.error(f'在社区中创建用户失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'创建用户失败: {str(e)}')