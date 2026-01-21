


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
    verify_password,
    verify_sms_code_dual_purpose,
    normalize_and_hash_phone
)
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

        # 使用 Repository 获取用户对象（符合 DDD 原则：Repository 用于数据访问）
        from app.infrastructure.persistence.repository_factory import RepositoryFactory
        user_repository = RepositoryFactory.get_user_repository()
        user = user_repository.find_by_phone_hash(phone_hash)

        if not user:
            current_app.logger.warning(f'用户不存在 - phone: {normalized_phone}')
            return make_err_response({}, '用户不存在')

        current_app.logger.info(f'找到用户 - user_id: {user.user_id}, nickname: {user.nickname}')

        # 使用 UseCase 确保用户有昵称
        from app.application.use_cases.auth import EnsureUserNicknameUseCase
        ensure_nickname_use_case = EnsureUserNicknameUseCase()
        ensure_nickname_use_case.execute(user)

        # 使用 UseCase 生成 token
        from app.application.use_cases.auth import GenerateAuthTokensUseCase
        generate_tokens_use_case = GenerateAuthTokensUseCase()
        tokens_result = generate_tokens_use_case.execute(user)

        if not tokens_result.is_success:
            current_app.logger.error(f'生成token失败: {tokens_result.message}')
            return make_err_response({}, tokens_result.message)

        token = tokens_result.data['token']
        refresh_token = tokens_result.data['refresh_token']

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

        # 使用 Repository 获取用户对象
        from app.infrastructure.persistence.repository_factory import RepositoryFactory
        user_repository = RepositoryFactory.get_user_repository()
        user = user_repository.find_by_phone_hash(phone_hash)

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
        # 使用 UseCase 确保用户有昵称
        from app.application.use_cases.auth import EnsureUserNicknameUseCase
        ensure_nickname_use_case = EnsureUserNicknameUseCase()
        ensure_nickname_use_case.execute(user)

        # 使用 UseCase 生成 token
        from app.application.use_cases.auth import GenerateAuthTokensUseCase
        generate_tokens_use_case = GenerateAuthTokensUseCase()
        tokens_result = generate_tokens_use_case.execute(user)

        if not tokens_result.is_success:
            current_app.logger.error(f'生成token失败: {tokens_result.message}')
            return make_err_response({}, tokens_result.message)

        token = tokens_result.data['token']
        refresh_token = tokens_result.data['refresh_token']

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
    手机号通用登录接口，支持三种场景：
    1. 老用户验证码登录：phone + code（二选一）
    2. 老用户密码登录：phone + password（二选一）
    3. 新用户首次登录/设置密码：phone + code + password（三者都需要）
    """
    current_app.logger.info('=== 开始执行手机号通用登录接口 ===')
    try:
        params = request.get_json() or {}
        phone = params.get('phone')
        code = params.get('code')
        password = params.get('password')
        current_app.logger.info(f'登录请求参数 - phone: {phone}, code: {bool(code)}, password: {bool(password)}')

        # 参数验证：phone 必填，code 和 password 至少一个必填
        if not phone:
            current_app.logger.warning('登录请求缺少phone参数')
            return make_err_response({}, '缺少phone参数')

        if not code and not password:
            current_app.logger.warning('登录请求缺少code或password参数')
            return make_err_response({}, '请提供验证码或密码进行登录')

        # 使用辅助函数标准化电话号码并生成 hash
        normalized_phone, phone_hash = normalize_and_hash_phone(phone, current_app.logger)

        # 使用 Repository 获取用户对象
        from app.infrastructure.persistence.repository_factory import RepositoryFactory
        user_repository = RepositoryFactory.get_user_repository()
        user = user_repository.find_by_phone_hash(phone_hash)

        # 场景判断
        has_code = bool(code)
        has_password = bool(password)

        # 场景 1: 只用验证码登录（老用户）
        if has_code and not has_password:
            current_app.logger.info('场景1: 验证码登录')
            return _handle_login_with_code_only(user, normalized_phone, phone, code)

        # 场景 2: 只用密码登录（老用户）
        if has_password and not has_code:
            current_app.logger.info('场景2: 密码登录')
            return _handle_login_with_password_only(user, normalized_phone, phone, password)

        # 场景 3: 同时提供验证码和密码（新用户首次登录或设置密码）
        current_app.logger.info('场景3: 验证码+密码登录')
        return _handle_login_with_code_and_password(user, normalized_phone, phone, code, password)

    except Exception as e:
        current_app.logger.error(f'手机号登录失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'登录失败: {str(e)}')


def _handle_login_with_code_only(user, normalized_phone, phone, code):
    """处理验证码登录（老用户场景）"""
    # 验证码验证
    current_app.logger.info('开始验证SMS验证码...')
    login_valid = _verify_sms_code(normalized_phone, 'login', code)
    register_valid = _verify_sms_code(normalized_phone, 'register', code)

    if not login_valid and not register_valid:
        current_app.logger.warning(f'SMS验证码验证失败 - phone: {normalized_phone}')
        return make_err_response({}, '验证码错误')

    current_app.logger.info('验证码验证通过，开始查询用户...')

    # 查找用户
    if not user:
        from app.infrastructure.persistence.repository_factory import RepositoryFactory
        user_repository = RepositoryFactory.get_user_repository()
        user = user_repository.find_by_phone_hash(normalize_and_hash_phone(phone, current_app.logger)[1])

    if not user:
        current_app.logger.warning(f'用户不存在 - phone: {normalized_phone}')
        return make_err_response({}, '用户不存在')

    return _complete_login(user, phone, 'login_phone_code')


def _handle_login_with_password_only(user, normalized_phone, phone, password):
    """处理密码登录（老用户场景）"""
    # 查找用户
    if not user:
        from app.infrastructure.persistence.repository_factory import RepositoryFactory
        user_repository = RepositoryFactory.get_user_repository()
        _, phone_hash = normalize_and_hash_phone(phone, current_app.logger)
        user = user_repository.find_by_phone_hash(phone_hash)

    if not user:
        current_app.logger.warning(f'用户不存在 - phone: {normalized_phone}')
        return make_err_response({'code': 'USER_NOT_FOUND'}, '账号不存在，请先注册')

    # 检查用户是否设置了密码
    if not user.password_hash or not user.password_salt:
        current_app.logger.warning(f'用户未设置密码 - user_id: {getattr(user, "user_id", "unknown")}')
        return make_err_response({}, '账号未设置密码，请使用验证码登录')

    # 验证密码
    if not verify_password(user, password, current_app.logger):
        return make_err_response({}, '密码不正确')

    current_app.logger.info('密码验证成功')
    return _complete_login(user, phone, 'login_phone_password')


def _handle_login_with_code_and_password(user, normalized_phone, phone, code, password):
    """处理验证码+密码登录（同时验证场景）"""
    # 验证码验证
    if not verify_sms_code_dual_purpose(phone, code, current_app.logger):
        current_app.logger.warning(f'验证码验证失败')
        return make_err_response({}, '验证码错误')

    current_app.logger.info('验证码验证通过')

    # 查找用户
    if not user:
        from app.infrastructure.persistence.repository_factory import RepositoryFactory
        user_repository = RepositoryFactory.get_user_repository()
        _, phone_hash = normalize_and_hash_phone(phone, current_app.logger)
        user = user_repository.find_by_phone_hash(phone_hash)

    if not user:
        current_app.logger.warning(f'用户不存在 - phone: {normalized_phone}')
        return make_err_response({'code': 'USER_NOT_FOUND'}, '账号不存在，请先注册')

    # 检查用户是否已设置密码
    if not user.password_hash or not user.password_salt:
        current_app.logger.warning(f'用户未设置密码 - user_id: {user.user_id}')
        return make_err_response({}, '账号未设置密码')

    # 验证密码
    if not verify_password(user, password, current_app.logger):
        return make_err_response({}, '密码不正确')

    current_app.logger.info('验证码和密码验证通过')
    return _complete_login(user, phone, 'login_phone')


def _complete_login(user, phone, login_type):
    """完成登录流程的公共逻辑"""
    # 使用 UseCase 确保用户有昵称
    from app.application.use_cases.auth import EnsureUserNicknameUseCase
    ensure_nickname_use_case = EnsureUserNicknameUseCase()
    ensure_nickname_use_case.execute(user)

    # 使用 UseCase 生成 token
    from app.application.use_cases.auth import GenerateAuthTokensUseCase
    generate_tokens_use_case = GenerateAuthTokensUseCase()
    tokens_result = generate_tokens_use_case.execute(user)

    if not tokens_result.is_success:
        current_app.logger.error(f'生成token失败: {tokens_result.message}')
        return make_err_response({}, tokens_result.message)

    token = tokens_result.data['token']
    refresh_token = tokens_result.data['refresh_token']

    _audit(user.user_id, login_type, {'phone': phone})
    current_app.logger.info(f'=== {login_type} 接口执行完成 ===')

    # 使用统一的响应格式，包含完整的用户信息
    response_data = _format_user_login_response(
        user, token, refresh_token, is_new_user=False
    )
    return make_succ_response(response_data)