"""
认证相关的辅助函数（纯工具函数）

已迁移到 UseCase 的函数：
- generate_auth_tokens -> GenerateAuthTokensUseCase
- ensure_user_nickname -> EnsureUserNicknameUseCase
- assign_user_to_default_community -> AssignUserToDefaultCommunityUseCase
- query_user_by_phone_hash_with_timing -> GetUserByPhoneHashUseCase

保留的纯工具函数：
- execute_timed_query - 带时间监控的查询执行
- verify_password - 密码验证
- verify_sms_code_dual_purpose - 短信验证码验证
- normalize_and_hash_phone - 电话号码标准化和hash生成
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


def normalize_and_hash_phone(phone, app_logger):
    """
    标准化电话号码并生成 hash
    
    Args:
        phone: 原始手机号
        app_logger: Flask 应用的 logger
        
    Returns:
        tuple: (normalized_phone, phone_hash)
    """
    from wxcloudrun.utils.validators import normalize_phone_number, generate_phone_hash
    
    # 标准化电话号码格式
    normalized_phone = normalize_phone_number(phone)
    app_logger.info(f'标准化后的手机号: {normalized_phone}')
    
    # 生成 phone_hash
    phone_hash = generate_phone_hash(normalized_phone)
    app_logger.info(f'生成phone_hash: {phone_hash[:20]}...')
    
    return normalized_phone, phone_hash

