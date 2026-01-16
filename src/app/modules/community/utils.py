"""
社区模块工具函数
包含权限检查等辅助函数
"""

import logging
from flask import current_app
from app.shared.constants.roles import Role

app_logger = logging.getLogger('log')


def _check_superadmin_permission(user):
    """检查用户是否为超级系统管理员"""
    if not user or user.role != Role.SUPER_ADMIN:  # 4是超级管理员
        current_app.logger.warning(f'用户 {user.user_id if user else None} 无超级管理员权限')
        from app.shared import make_err_response
        return make_err_response({}, '无权限访问')
    return None