"""
认证相关的辅助函数
用于减少认证模块中的重复代码
"""

import logging
import time
from hashlib import sha256

logger = logging.getLogger(__name__)


def execute_timed_query(query_func, query_name, *args, **kwargs):
    """
    执行带时间监控的数据库查询
    
    Args:
        query_func: 查询函数
        query_name: 查询名称（用于日志）
        *args: 查询函数的参数
        **kwargs: 查询函数的关键字参数
        
    Returns:
        查询结果
        
    Raises:
        Exception: 数据库查询异常
    """
    try:
        logger.info(f'开始执行{query_name}...')
        start_time = time.time()
        result = query_func(*args, **kwargs)
        query_time = time.time() - start_time
        logger.info(f'{query_name}完成，耗时: {query_time:.2f}秒')
        
        # 检查查询时间是否异常长
        if query_time > 3.0:
            logger.warning(f'{query_name}耗时过长: {query_time:.2f}秒')
        
        return result
    except Exception as e:
        logger.error(f'{query_name}异常: {str(e)}', exc_info=True)
        raise


def generate_auth_tokens(user, app_logger):
    """
    生成 JWT token 和 refresh token
    
    Args:
        user: 用户对象
        app_logger: Flask 应用的 logger
        
    Returns:
        tuple: (token, refresh_token, error_response)
    """
    from app.shared.utils.auth import generate_jwt_token, generate_refresh_token
    from wxcloudrun.user_service import UserService
    
    app_logger.info('开始生成JWT token...')
    token, error_response = generate_jwt_token(user, expires_hours=2)
    if error_response:
        return None, None, error_response
    
    refresh_token = generate_refresh_token(user, expires_days=7)
    UserService.update_user_by_id(user)
    
    app_logger.info('保存refresh token到数据库...')
    return token, refresh_token, None


def verify_password(user, password, app_logger):
    """
    验证用户密码
    
    Args:
        user: 用户对象
        password: 待验证的密码
        app_logger: Flask 应用的 logger
        
    Returns:
        bool: 密码是否正确
    """
    pwd_hash = sha256(
        f"{password}:{user.password_salt}".encode('utf-8')).hexdigest()
    
    if pwd_hash != user.password_hash:
        app_logger.warning(f'密码验证失败 - user_id: {user.user_id}')
        return False
    
    return True


def ensure_user_nickname(user, app_logger):
    """
    确保用户有昵称，如果没有则生成默认昵称
    
    Args:
        user: 用户对象
        app_logger: Flask 应用的 logger
    """
    from wxcloudrun.utils.validators import _gen_phone_nickname
    
    if not user.nickname:
        user.nickname = _gen_phone_nickname()
        UserService.update_user_by_id(user)
        app_logger.info(f'已更新用户昵称: {user.nickname}')


def verify_sms_code_dual_purpose(phone, code, app_logger):
    """
    验证短信验证码（支持 login 或 register 类型）
    
    Args:
        phone: 手机号
        code: 验证码
        app_logger: Flask 应用的 logger
        
    Returns:
        bool: 验证码是否有效
    """
    from wxcloudrun.utils.validators import _verify_sms_code
    
    # 标准化电话号码格式
    from wxcloudrun.utils.validators import normalize_phone_number
    normalized_phone = normalize_phone_number(phone)
    
    app_logger.info('开始验证SMS验证码...')
    login_valid = _verify_sms_code(normalized_phone, 'login', code)
    register_valid = _verify_sms_code(normalized_phone, 'register', code)
    
    app_logger.info(f'SMS验证结果 - login_valid: {login_valid}, register_valid: {register_valid}')
    
    if not login_valid and not register_valid:
        app_logger.warning(f'SMS验证码验证失败 - phone: {normalized_phone}, code: {code}')
        return False
    
    return True