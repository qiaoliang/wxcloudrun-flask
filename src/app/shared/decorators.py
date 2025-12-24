"""
装饰器模块
包含所有视图装饰器
"""

from functools import wraps
import logging
from flask import request
from app.shared.utils.auth import verify_token
from wxcloudrun.community_service import CommunityService

app_logger = logging.getLogger('log')


def login_required(f):
    """
    登录验证装饰器
    验证请求中的JWT token，并将解码后的用户信息传递给视图函数
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        decoded, error_response = verify_token()
        if error_response:
            return error_response
        return f(decoded, *args, **kwargs)
    return decorated_function


def require_token():
    """
    Token验证装饰器
    验证请求中的JWT token，返回解码后的用户信息和错误响应
    """
    return verify_token()


def require_community_staff_member():
    """
    社区工作人员权限验证装饰器
    验证用户是否为社区工作人员或超级管理员
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 验证token
            decoded, error_response = verify_token()
            if error_response:
                return error_response
            
            user_id = decoded['user_id']
            
            # 从请求中获取community_id
            from flask import request
            community_id = request.view_args.get('community_id') or request.json.get('community_id')
            if not community_id:
                from app.shared.response import make_err_response
                return make_err_response('缺少社区ID参数')
            
            # 验证权限
            if not CommunityService.has_community_permission(user_id, community_id):
                from app.shared.response import make_err_response
                return make_err_response('无权限访问该社区功能')
            
            return f(decoded, *args, **kwargs)
        return decorated_function
    return decorator


def require_community_membership():
    """
    社区成员权限验证装饰器
    验证用户是否属于指定社区
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 验证token
            decoded, error_response = verify_token()
            if error_response:
                return error_response
            
            user_id = decoded['user_id']
            
            # 从请求中获取community_id
            from flask import request
            community_id = request.view_args.get('community_id') or request.json.get('community_id')
            if not community_id:
                from app.shared.response import make_err_response
                return make_err_response('缺少社区ID参数')
            
            # 验证社区成员关系
            if not CommunityService.verify_user_community_access(user_id, community_id):
                from app.shared.response import make_err_response
                return make_err_response('无权限访问该社区')
            
            return f(decoded, *args, **kwargs)
        return decorated_function
    return decorator