"""
认证工具模块
包含认证相关的工具函数
"""

import logging
import jwt
from flask import request
from wxcloudrun import app
from wxcloudrun.dao import query_user_by_openid
from wxcloudrun.response import make_err_response
from config_manager import get_token_secret

app_logger = logging.getLogger('log')


def verify_token():
    """
    验证JWT token并返回解码后的用户信息
    """
    # 获取请求体参数 - 对于GET请求，通常没有请求体
    try:
        if request.method in ['POST', 'PUT', 'PATCH']:  # 只对有请求体的方法获取JSON
            params = request.get_json() if request.is_json else {}
        else:
            params = {}  # GET请求通常没有请求体
    except Exception as e:
        app.logger.warning(f'解析请求JSON失败: {str(e)}')
        params = {}

    # 验证token
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        header_token = auth_header[7:]  # 去掉 'Bearer ' 前缀
    else:
        header_token = auth_header
    token = params.get('token') or header_token

    if not token:
        app.logger.warning('请求中缺少token参数')
        return None, make_err_response({}, '缺少token参数')

    # 检查token是否包含额外的引号并去除
    if token and token.startswith('"') and token.endswith('"'):
        app.logger.info('检测到token包含额外引号，正在去除...')
        token = token[1:-1]  # 去除首尾的引号
        app.logger.info(f'去除引号后的token: {token[:50]}...')
    else:
        app.logger.info(f'token不包含额外引号或为空，无需处理')

    try:
        # 从配置管理器获取TOKEN_SECRET
        try:
            token_secret = get_token_secret()
        except ValueError as e:
            app.logger.error(f'获取TOKEN_SECRET失败: {str(e)}')
            return None, make_err_response({}, '服务器配置错误')

        app.logger.debug(f'使用TOKEN_SECRET进行token验证')

        # 解码token
        decoded = jwt.decode(
            token,
            token_secret,
            algorithms=['HS256']
        )
        openid = decoded.get('openid')

        if not openid:
            app.logger.error('解码后的token中未找到openid')
            return None, make_err_response({}, 'token无效')

        return decoded, None
    except jwt.ExpiredSignatureError:
        return None, make_err_response({}, 'token已过期')
    except jwt.InvalidSignatureError:
        return None, make_err_response({}, 'token签名无效')
    except jwt.DecodeError:
        return None, make_err_response({}, 'token格式错误')
    except jwt.InvalidTokenError:
        return None, make_err_response({}, 'token无效')
    except Exception as e:
        app.logger.error(f'JWT验证时发生错误: {str(e)}', exc_info=True)
        return None, make_err_response({}, f'JWT验证失败: {str(e)}')

def require_role(required_role):
    """
    装饰器：要求用户具有特定角色
    role参数可以是：
    - 整数：具体的角色值
    - 列表：多个角色值之一即可
    - 字符串：角色名称
    """
    def decorator(f):
        from functools import wraps

        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 验证token
            decoded, error_response = verify_token()
            if error_response:
                return error_response

            user_id = decoded.get('user_id')
            from database.models import User
            user = User.query.get(user_id)

            if not user:
                return make_err_response({}, '用户不存在')

            # 检查角色
            if isinstance(required_role, int):
                if user.role != required_role:
                    return make_err_response({}, '权限不足')
            elif isinstance(required_role, list):
                if user.role not in required_role:
                    return make_err_response({}, '权限不足')
            elif isinstance(required_role, str):
                # 检查角色名称
                if user.role_name != required_role:
                    return make_err_response({}, '权限不足')

            # 将用户信息添加到请求上下文
            request.current_user = user
            return f(*args, **kwargs)

        return decorated_function
    return decorator


def require_community_admin():
    """
    装饰器：要求用户是社区管理员（包括超级管理员）
    """
    def decorator(f):
        from functools import wraps

        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 验证token
            decoded, error_response = verify_token()
            if error_response:
                return error_response

            user_id = decoded.get('user_id')
            from database.models import User
            user = User.query.get(user_id)

            if not user:
                return make_err_response({}, '用户不存在')

            # 检查是否为社区管理员或超级管理员
            if user.role not in [3, 4]:  # 社区管理员或超级管理员
                return make_err_response({}, '需要社区管理员权限')

            # 将用户信息添加到请求上下文
            request.current_user = user
            return f(*args, **kwargs)

        return decorated_function
    return decorator


def require_super_admin():
    """
    装饰器：要求用户是超级管理员
    """
    return require_role(4)  # 角色值为4的是超级管理员


def check_community_permission(community_id):
    """
    检查当前用户是否有权限管理指定社区
    """
    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response, None

    user_id = decoded.get('user_id')
    from database.models import User
    user = User.query.get(user_id)

    if not user:
        return make_err_response({}, '用户不存在'), None

    # 检查权限
    if not user.can_manage_community(community_id):
        return make_err_response({}, '权限不足'), None

    return None, user


def get_current_user():
    """
    获取当前登录用户
    """
    decoded, error_response = verify_token()
    if error_response:
        return None

    user_id = decoded.get('user_id')
    from database.models import User
    return User.query.get(user_id)