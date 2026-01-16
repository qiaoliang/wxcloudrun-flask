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

    app_logger.info('开始生成JWT token...')
    token, error_response = generate_jwt_token(user, expires_hours=2)
    if error_response:
        return None, None, error_response

    refresh_token = generate_refresh_token(user, expires_days=7)
    from app.application.use_cases.user import UpdateUserUseCase
    update_use_case = UpdateUserUseCase()
    update_result = update_use_case.execute(user)
    if not update_result.is_success:
        app_logger.warning(f'更新用户信息失败: {update_result.message}')

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
        from app.application.use_cases.user import UpdateUserUseCase
        update_use_case = UpdateUserUseCase()
        update_result = update_use_case.execute(user)
        if not update_result.is_success:
            app_logger.warning(f'更新用户昵称失败: {update_result.message}')
        else:
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


def assign_user_to_default_community(user, app_logger):
    """
    自动分配用户到默认社区
    
    Args:
        user: 用户对象
        app_logger: Flask 应用的 logger
    """
    from wxcloudrun.community_service import CommunityService
    from const_default import DEFAULT_COMMUNITY_NAME
    
    try:
        CommunityService.assign_user_to_community(user, DEFAULT_COMMUNITY_NAME)
        app_logger.info(f'新用户已自动分配到默认社区，用户ID: {user.user_id}')
    except Exception as e:
        app_logger.error(f'自动分配社区失败: {str(e)}', exc_info=True)
        # 不影响登录流程，只记录错误


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


def query_user_by_phone_hash_with_timing(phone_hash, app_logger):
    """
    通过 phone_hash 查询用户（带时间监控）
    
    Args:
        phone_hash: 手机号 hash
        app_logger: Flask 应用的 logger
        
    Returns:
        User: 用户对象，如果不存在则返回 None
    """
    from app.application.use_cases.user import GetUserByPhoneHashUseCase
    from database.flask_models import db, User

    get_user_use_case = GetUserByPhoneHashUseCase()
    result = get_user_use_case.execute(phone_hash)

    if result.is_success:
        # UseCase 返回的是字典，需要重新查询 User 对象
        user_id = result.data.get('user_id')
        if user_id:
            stmt = db.session.execute(
                db.select(User).where(User.user_id == user_id)
            )
            return stmt.scalar_one_or_none()
    return None