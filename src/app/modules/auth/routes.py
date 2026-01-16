


"""
认证模块路由
包含登录、注册、token管理等功能
"""

import logging
import datetime
import jwt
from flask import request, current_app
from . import auth_bp
from .services import _format_user_login_response
from app.shared import make_succ_response, make_err_response
from app.shared.utils.auth import generate_jwt_token, generate_refresh_token, verify_token
from app.shared.utils.auth_helpers import (
    generate_auth_tokens,
    verify_password,
    ensure_user_nickname,
    verify_sms_code_dual_purpose,
    assign_user_to_default_community,
    normalize_and_hash_phone,
    query_user_by_phone_hash_with_timing
)
from database.flask_models import db, User
from wxcloudrun.utils.validators import _verify_sms_code, _audit, _gen_phone_nickname
from const_default import DEFAULT_COMMUNITY_NAME
from error_code import INVALID_CAPTCHA

app_logger = logging.getLogger('log')

# 导入速率限制扩展
from app.extensions import limiter


@auth_bp.route('/auth/login_wechat', methods=['POST'])
@limiter.limit("5 per minute;20 per hour", error_message="登录请求过于频繁，请稍后再试")
def login_wechat():
    """
    微信登录接口，通过code获取用户信息并返回token
    :return: token
    """
    current_app.logger.info('=== 开始执行微信登录接口 ===')

    # 获取请求体参数
    params = request.get_json()
    if not params:
        current_app.logger.warning('登录请求缺少请求体参数')
        return make_err_response({}, '缺少请求体参数')

    code = params.get('code')
    if not code:
        current_app.logger.warning('登录请求缺少code参数')
        return make_err_response({}, '缺少code参数')

    # 获取可选的用户信息参数
    nickname = params.get('nickname')
    avatar_url = params.get('avatar_url')

    # 调用应用服务层处理登录逻辑
    from app.application.use_cases.auth import LoginWeChatUseCase

    use_case = LoginWeChatUseCase()
    result = use_case.execute(
        code=code,
        nickname=nickname,
        avatar_url=avatar_url
    )

    if result.is_success:
        current_app.logger.info(f'微信登录成功 - {result.data.get("login_type")}')
        return make_succ_response(result.data)
    else:
        current_app.logger.warning(f'微信登录失败: {result.message}')
        return make_err_response({}, result.message)


@auth_bp.route('/auth/refresh_token', methods=['POST'])
@limiter.limit("20 per minute;200 per hour", error_message="刷新请求过于频繁，请稍后再试")
def refresh_token():
    """
    刷新token接口，使用refresh token获取新的access token
    """
    current_app.logger.info('=== 开始执行刷新Token接口 ===')

    # 获取请求体参数
    params = request.get_json()
    if not params:
        current_app.logger.warning('刷新Token请求缺少请求体参数')
        return make_err_response({}, '缺少请求体参数')

    refresh_token = params.get('refresh_token')
    if not refresh_token:
        current_app.logger.warning('刷新Token请求缺少refresh_token参数')
        return make_err_response({}, '缺少refresh_token参数')

    # 调用应用服务层处理刷新 token 逻辑
    from app.application.use_cases.auth import RefreshTokenUseCase

    use_case = RefreshTokenUseCase()
    result = use_case.execute(refresh_token=refresh_token)

    if result.is_success:
        current_app.logger.info('刷新 Token 成功')
        return make_succ_response(result.data)
    else:
        current_app.logger.warning(f'刷新 Token 失败: {result.message}')
        return make_err_response({}, result.message)


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    用户登出接口，清除refresh token
    """
    current_app.logger.info('=== 开始执行登出接口 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    openid = decoded.get('openid')
    if not openid:
        return make_err_response({}, 'token无效')

    # 调用应用服务层处理登出逻辑
    from app.application.use_cases.auth import LogoutUseCase

    use_case = LogoutUseCase()
    result = use_case.execute(openid=openid)

    if result.is_success:
        current_app.logger.info('登出成功')
        return make_succ_response({'message': result.message})
    else:
        current_app.logger.warning(f'登出失败: {result.message}')
        return make_err_response({}, result.message)


@auth_bp.route('/auth/register_phone', methods=['POST'])
@limiter.limit("5 per minute;20 per hour", error_message="注册请求过于频繁，请稍后再试")
def register_phone():
    """
    手机号注册接口
    """
    current_app.logger.info('=== 开始执行手机号注册接口 ===')

    try:
        params = request.get_json() or {}
        phone = params.get('phone') or params.get('phone_number')
        code = params.get('code') or params.get('sms_code')
        nickname = params.get('nickname')
        avatar_url = params.get('avatar_url')
        password = params.get('password')

        if not phone or not code:
            current_app.logger.warning('注册请求缺少phone或code参数')
            return make_err_response({}, '缺少phone或code参数')

        # 调用应用服务层处理注册逻辑
        from app.application.use_cases.auth import RegisterPhoneUseCase

        use_case = RegisterPhoneUseCase()
        result = use_case.execute(
            phone=phone,
            code=code,
            nickname=nickname,
            avatar_url=avatar_url,
            password=password
        )

        if result.is_success:
            current_app.logger.info('手机号注册成功')
            return make_succ_response(result.data)
        else:
            current_app.logger.warning(f'手机号注册失败: {result.message}')
            return make_err_response({}, result.message)

    except Exception as e:
        current_app.logger.error(f'手机号注册失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'注册失败: {str(e)}')


@auth_bp.route('/auth/login_phone_code', methods=['POST'])
@limiter.limit("5 per minute;20 per hour", error_message="登录请求过于频繁，请稍后再试")
def login_phone_code():
    current_app.logger.info('=== 开始执行手机号验证码登录接口 ===')
    try:
        params = request.get_json() or {}
        phone = params.get('phone') or params.get('phone_number')
        code = params.get('code') or params.get('sms_code')
        current_app.logger.info(f'登录请求参数 - phone: {phone}, code: {code}')

        if not phone or not code:
            current_app.logger.warning('登录请求缺少phone或code参数')
            return make_err_response({}, '缺少phone或code参数')

        # 使用辅助函数标准化电话号码并生成 hash
        normalized_phone, phone_hash = normalize_and_hash_phone(phone, current_app.logger)

        # 验证码验证 - 添加详细日志
        current_app.logger.info('开始验证SMS验证码...')
        login_valid = _verify_sms_code(normalized_phone, 'login', code)
        register_valid = _verify_sms_code(normalized_phone, 'register', code)
        current_app.logger.info(f'SMS验证结果 - login_valid: {login_valid}, register_valid: {register_valid}')

        if not login_valid and not register_valid:
            current_app.logger.warning(f'SMS验证码验证失败 - phone: {normalized_phone}, code: {code}')
            return make_err_response({}, 'INVALID_CAPTCHA')

        current_app.logger.info('SMS验证码验证通过，开始查询用户...')

        # 使用辅助函数执行带时间监控的数据库查询
        user = query_user_by_phone_hash_with_timing(phone_hash, current_app.logger)

        if not user:
            current_app.logger.warning(f'用户不存在 - phone: {normalized_phone}')
            return make_err_response({}, '用户不存在')

        current_app.logger.info(f'找到用户 - user_id: {user.user_id}, nickname: {user.nickname}')

        # 使用辅助函数确保用户有昵称
        ensure_user_nickname(user, current_app.logger)

        # 使用辅助函数生成token
        token, refresh_token, error_response = generate_auth_tokens(user, current_app.logger)
        if error_response:
            return error_response

        _audit(user.user_id, 'login_phone_code', {'phone': phone})
        current_app.logger.info('=== 手机号验证码登录接口执行完成 ===')

        # 使用统一的响应格式，包含完整的用户信息
        response_data = _format_user_login_response(
            user, token, refresh_token, is_new_user=False
        )
        return make_succ_response(response_data)
    except Exception as e:
        current_app.logger.error(f'验证码登录失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'登录失败: {str(e)}')


@auth_bp.route('/auth/login_phone_password', methods=['POST'])
@limiter.limit("5 per minute;20 per hour", error_message="登录请求过于频繁，请稍后再试")
def login_phone_password():
    current_app.logger.info('=== 开始执行手机号密码登录接口 ===')
    try:
        params = request.get_json() or {}
        phone = params.get('phone')
        password = params.get('password')
        current_app.logger.info(f'登录请求参数 - phone: {phone}, password: {"*" * len(password) if password else "None"}')

        if not phone or not password:
            current_app.logger.warning('登录请求缺少phone或password参数')
            return make_err_response({}, '缺少phone或password参数')

        # 使用辅助函数标准化电话号码并生成 hash
        normalized_phone, phone_hash = normalize_and_hash_phone(phone, current_app.logger)

        # 使用辅助函数执行带时间监控的数据库查询
        user = query_user_by_phone_hash_with_timing(phone_hash, current_app.logger)

        if not user:
            current_app.logger.warning(f'用户不存在 - phone: {normalized_phone}')
            return make_err_response({'code': 'USER_NOT_FOUND'}, '账号不存在，请先注册')
        if not user.password_hash or not user.password_salt:
            current_app.logger.warning(f'用户未设置密码 - user_id: {user.user_id}')
            return make_err_response({}, '账号未设置密码')

        # 使用辅助函数验证密码
        if not verify_password(user, password, current_app.logger):
            return make_err_response({}, '密码不正确')

        current_app.logger.info(f'密码验证成功，开始处理用户信息 - user_id: {user.user_id}')
        # 使用辅助函数确保用户有昵称
        ensure_user_nickname(user, current_app.logger)

        # 使用辅助函数生成token
        token, refresh_token, error_response = generate_auth_tokens(user, current_app.logger)
        if error_response:
            return error_response
        _audit(user.user_id, 'login_phone_password', {'phone': phone})

        current_app.logger.info('=== 手机号密码登录接口执行完成 ===')

        # 使用统一的响应格式，包含完整的用户信息
        response_data = _format_user_login_response(
            user, token, refresh_token, is_new_user=False
        )
        return make_succ_response(response_data)
    except Exception as e:
        current_app.logger.error(f'密码登录失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'登录失败: {str(e)}')


@auth_bp.route('/auth/login_phone', methods=['POST'])
@limiter.limit("5 per minute;20 per hour", error_message="登录请求过于频繁，请稍后再试")
def login_phone():
    """
    手机号登录：需要同时验证验证码和密码
    """
    current_app.logger.info('=== 开始执行手机号登录接口（验证验证码+密码） ===')
    try:
        params = request.get_json() or {}
        phone = params.get('phone')
        code = params.get('code')
        password = params.get('password')
        current_app.logger.info(f'登录请求参数 - phone: {phone}, code: {code}, password: {"*" * len(password) if password else "None"}')

        # 参数验证
        if not phone or not code or not password:
            current_app.logger.warning('登录请求缺少phone、code或password参数')
            return make_err_response({}, '缺少phone、code或password参数')

        # 使用辅助函数验证验证码（支持 login 或 register 类型）
        if not verify_sms_code_dual_purpose(phone, code, current_app.logger):
            current_app.logger.warning(f'验证码验证失败')
            return make_err_response({}, 'INVALID_CAPTCHA')
        current_app.logger.info('验证码验证通过')

        # 使用辅助函数标准化电话号码并生成 hash
        normalized_phone, phone_hash = normalize_and_hash_phone(phone, current_app.logger)

        # 使用辅助函数执行带时间监控的数据库查询
        user = query_user_by_phone_hash_with_timing(phone_hash, current_app.logger)

        if not user:
            current_app.logger.warning(f'用户不存在 - phone: {normalized_phone}')
            return make_err_response({'code': 'USER_NOT_FOUND'}, '账号不存在，请先注册')
        if not user.password_hash or not user.password_salt:
            current_app.logger.warning(f'用户未设置密码 - user_id: {user.user_id}')
            return make_err_response({}, '账号未设置密码')

        # 使用辅助函数验证密码
        if not verify_password(user, password, current_app.logger):
            return make_err_response({}, '密码不正确')

        current_app.logger.info(f'密码验证成功，开始处理用户信息 - user_id: {user.user_id}')
        # 使用辅助函数确保用户有昵称
        ensure_user_nickname(user, current_app.logger)

        # 使用辅助函数生成token
        token, refresh_token, error_response = generate_auth_tokens(user, current_app.logger)
        if error_response:
            return error_response
        refresh_token = generate_refresh_token(user, expires_days=7)

        current_app.logger.info('保存refresh token到数据库...')
        # 使用 UpdateUserUseCase 更新用户信息
        from app.application.use_cases.user import UpdateUserUseCase
        update_use_case = UpdateUserUseCase()
        update_result = update_use_case.execute(user)
        if not update_result.is_success:
            current_app.logger.warning(f'更新用户信息失败: {update_result.message}')
        _audit(user.user_id, 'login_phone', {'phone': phone})

        current_app.logger.info('=== 手机号登录接口执行完成 ===')

        # 使用统一的响应格式，包含完整的用户信息
        response_data = _format_user_login_response(
            user, token, refresh_token, is_new_user=False
        )
        return make_succ_response(response_data)
    except Exception as e:
        current_app.logger.error(f'手机号登录失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'登录失败: {str(e)}')