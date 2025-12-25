"""
装饰器模块
包含所有视图装饰器
"""

from functools import wraps
import logging
from flask import request
from database.flask_models import db
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
    支持从community_id参数或rule_id参数获取社区ID
    超级系统管理员（role=4）可以直接通过，不需要检查社区权限
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 验证token
            decoded, error_response = verify_token()
            if error_response:
                return error_response

            user_id = decoded['user_id']

            # 检查是否为超级系统管理员
            from database.flask_models import User
            user = db.session.get(User, user_id)
            if user and user.role == 4:  # 超级系统管理员
                return f(decoded, *args, **kwargs)

            # 从请求中获取community_id
            from flask import request
            from database.flask_models import CommunityCheckinRule

            # 优先从路径参数、查询参数、请求体中获取community_id
            community_id = (request.view_args.get('community_id') or
                          request.args.get('community_id') or
                          request.json.get('community_id') if request.is_json else None)

            # 如果没有community_id，尝试从rule_id获取
            if not community_id:
                rule_id = request.view_args.get('rule_id')
                if rule_id:
                    # 从数据库查询规则获取community_id
                    rule = db.session.get(CommunityCheckinRule, rule_id)
                    if rule:
                        community_id = rule.community_id

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