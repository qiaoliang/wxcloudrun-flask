"""
装饰器模块
包含所有视图装饰器
"""

from functools import wraps
import logging
from flask import request
from wxcloudrun.utils.auth import verify_token

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