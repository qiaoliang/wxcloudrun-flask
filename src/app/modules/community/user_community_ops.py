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
from wxcloudrun.community_service import CommunityService
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
        if not CommunityService.verify_user_community_access(user_id, user.community_id):
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
        success = CommunityService.switch_user_community(user_id, community_id)

        if success:
            # 记录审计日志
            _audit(user_id, 'switch_community', {
                'community_id': community_id
            })

            current_app.logger.info(f'切换用户社区成功: user_id={user_id}, community_id={community_id}')
            return make_succ_response({'message': '切换成功'})
        else:
            return make_err_response({}, '切换失败')

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
        if not CommunityService.has_community_permission(operator_id, community_id):
            return make_err_response({}, '无权限访问该社区')

        # 创建用户
        user = CommunityService.create_user_in_community(community_id, user_data, operator_id)
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