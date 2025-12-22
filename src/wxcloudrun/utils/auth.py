"""
认证工具模块
包含认证相关的工具函数
"""

import logging
import jwt
from flask import request
from wxcloudrun import app
from wxcloudrun.user_service import UserService
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
        user_id = decoded.get('user_id')

        # 对于手机号注册的用户，openid可能为空，但user_id必须存在
        if not user_id:
            app.logger.error('解码后的token中未找到user_id')
            return None, make_err_response({}, 'token无效')

        # 如果openid为空，记录日志但不阻止验证（手机号注册用户）
        if not openid:
            app.logger.info(f'用户{user_id}使用手机号注册，openid为空')

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
            from database.flask_models import User
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
            from database.flask_models import User
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


def require_community_staff():
    """
    装饰器：要求用户是社区工作人员（专员、主管、超级管理员）
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
            from database.flask_models import User
            user = User.query.get(user_id)

            if not user:
                return make_err_response({}, '用户不存在')

            # 检查是否为社区工作人员或超级管理员
            if user.role not in [2, 3, 4]:  # 社区专员、社区主管、超级管理员
                return make_err_response({}, '需要社区工作人员权限')

            # 将用户信息添加到请求上下文
            request.current_user = user
            return f(*args, **kwargs)

        return decorated_function
    return decorator


def require_community_manager():
    """
    装饰器：要求用户是社区主管或超级管理员
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
            from database.flask_models import User
            user = User.query.get(user_id)

            if not user:
                return make_err_response({}, '用户不存在')

            # 检查是否为社区主管或超级管理员
            if user.role not in [3, 4]:  # 社区主管、超级管理员
                return make_err_response({}, '需要社区主管权限')

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
    from database.flask_models import User
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
    from database.flask_models import User
    return User.query.get(user_id)


def generate_jwt_token(user, expires_hours=2):
    """
    生成 JWT access token

    Args:
        user: User 对象，需要包含 wechat_openid 和 user_id
        expires_hours: token 过期时间（小时），默认 2 小时

    Returns:
        tuple: (token, error_response)
            - token: 生成的 JWT token 字符串，如果失败则为 None
            - error_response: 错误响应对象，如果成功则为 None
    """
    import datetime

    # 构建 token payload
    token_payload = {
        'openid': user.wechat_openid,
        'user_id': user.user_id,
        'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=expires_hours)
    }
    app.logger.info(f'JWT token payload: {token_payload}')

    # 从配置管理器获取 TOKEN_SECRET
    try:
        token_secret = get_token_secret()
    except ValueError as e:
        app.logger.error(f'获取TOKEN_SECRET失败: {str(e)}')
        return None, make_err_response({}, '服务器配置错误')

    app.logger.info(f'使用配置的TOKEN_SECRET: {token_secret[:20]}...')

    # 生成 JWT token
    token = jwt.encode(token_payload, token_secret, algorithm='HS256')
    return token, None


def generate_refresh_token(user, expires_days=7):
    """
    生成 refresh token 并更新到用户对象

    Args:
        user: User 对象，将更新其 refresh_token 和 refresh_token_expire 字段
        expires_days: refresh token 过期时间（天），默认 7 天

    Returns:
        str: 生成的 refresh token 字符串

    Note:
        此函数会修改 user 对象但不会提交到数据库，调用方需要自行调用 update_user_by_id() 保存
    """
    import datetime
    import secrets

    # 生成 refresh token
    refresh_token = secrets.token_urlsafe(32)
    app.logger.info(f'生成的refresh_token: {refresh_token[:20]}...')

    # 设置过期时间
    refresh_token_expire = datetime.datetime.now() + datetime.timedelta(days=expires_days)

    # 更新用户对象（但不提交到数据库）
    user.refresh_token = refresh_token
    user.refresh_token_expire = refresh_token_expire

    return refresh_token