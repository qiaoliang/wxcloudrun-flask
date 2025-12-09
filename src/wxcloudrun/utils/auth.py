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


def query_user_by_refresh_token(refresh_token):
    """
    根据refresh token查询用户
    """
    try:
        from wxcloudrun.dao import session
        from wxcloudrun.model import User
        user = session.query(User).filter(
            User.refresh_token == refresh_token).first()
        return user
    except Exception as e:
        app.logger.error(f'查询用户失败: {str(e)}')
        return None