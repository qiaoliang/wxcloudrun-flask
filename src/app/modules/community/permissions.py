"""
社区权限检查路由
包含社区访问权限检查功能
"""

import logging
from flask import current_app
from . import community_bp
from app.shared import make_succ_response, make_err_response
from app.shared.utils.auth import verify_token
from database.flask_models import db, User

app_logger = logging.getLogger('log')


@community_bp.route('/communities/manage/<int:community_id>/access-check', methods=['GET'])
def check_community_access(community_id):
    """检查社区访问权限"""
    current_app.logger.info(f'=== 开始检查社区访问权限: {community_id} ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    current_app.logger.info(f'用户ID: {user_id}')

    try:
        # 检查权限
        from app.application.use_cases.community import CheckCommunityPermissionUseCase
        check_permission_use_case = CheckCommunityPermissionUseCase()
        permission_result = check_permission_use_case.execute(user_id, community_id)
        has_permission = permission_result.data.get('has_permission', False) if permission_result.is_success else False

        # 获取用户在社区中的角色
        user_role = None
        if has_permission:
            stmt = db.session.execute(
                db.select(User).where(User.user_id == user_id)
            )
            user = stmt.scalar_one_or_none()
            if user:
                user_role = user.role_name

        response_data = {
            'community_id': community_id,
            'has_permission': has_permission,
            'user_role': user_role
        }

        current_app.logger.info(f'社区访问权限检查完成: community_id={community_id}, has_permission={has_permission}, user_role={user_role}')
        return make_succ_response(response_data)

    except Exception as e:
        current_app.logger.error(f'检查社区访问权限失败: {str(e)}', exc_info=True)
        return make_err_response({}, '权限检查失败')