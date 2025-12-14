"""
认证视图模块
包含登录、注册、token管理等功能
"""

import logging
import datetime
import secrets
import jwt
import os
from hashlib import sha256
from flask import request
from wxcloudrun import app
from wxcloudrun.response import make_succ_response, make_err_response
from wxcloudrun.dao import query_user_by_openid, insert_user, update_user_by_id
from database.models import User
from wxcloudrun.utils.validators import _verify_sms_code, _audit, _gen_phone_nickname, _hash_code, normalize_phone_number
from config_manager import get_token_secret

app_logger = logging.getLogger('log')


def _format_user_login_response(user, token, refresh_token, is_new_user=False):
    """统一格式化登录响应"""
    return {
        'token': token,
        'refresh_token': refresh_token,
        'user_id': user.user_id,
        'wechat_openid': user.wechat_openid,
        'phone_number': user.phone_number,
        'nickname': user.nickname,
        'avatar_url': user.avatar_url,
        'role': user.role_name,
        'login_type': 'new_user' if is_new_user else 'existing_user'
    }


@app.route('/api/login', methods=['POST'])
def login():
    """
    登录接口，通过code获取用户信息并返回token
    :return: token
    """
    from const_default import DEFUALT_COMMUNITY_NAME
    app.logger.info('=== 开始执行登录接口 ===')

    # 在日志中打印登录请求
    request_params = request.get_json()
    app.logger.info(f'login 请求参数: {request_params}')

    # 获取请求体参数
    params = request.get_json()
    if not params:
        app.logger.warning('登录请求缺少请求体参数')
        return make_err_response({}, '缺少请求体参数')

    app.logger.info('成功获取请求参数，开始检查code参数')

    code = params.get('code')
    if not code:
        app.logger.warning('登录请求缺少code参数')
        return make_err_response({}, '缺少code参数')

    # 打印code用于调试
    app.logger.info(f'获取到的code: {code}')

    # 获取必需的用户信息
    nickname = params.get('nickname')
    if not nickname:
        app.logger.warning('登录请求缺少nickname参数')
        return make_err_response({}, '缺少nickname参数')

    avatar_url = params.get('avatar_url')
    if not avatar_url:
        app.logger.warning('登录请求缺少avatar_url参数')
        return make_err_response({}, '缺少avatar_url参数')

    app.logger.info(
        f'获取到的用户信息 - nickname: {nickname}, avatar_url: {avatar_url}')

    app.logger.info('开始调用微信API获取用户openid和session_key')

    # 调用微信API获取用户信息
    try:
        # 使用新的微信API模块，根据环境变量智能选择真实或模拟API
        from wxcloudrun.wxchat_api import get_user_info_by_code
        from wxcloudrun.user_service import UserService
        app.logger.info('正在通过微信API模块获取用户信息...')
        wx_data = get_user_info_by_code(code)

        app.logger.info(f'微信API响应数据类型: {type(wx_data)}')
        app.logger.info(f'微信API响应内容: {wx_data}')

        # 检查微信API返回的错误
        if 'errcode' in wx_data:
            app.logger.error(
                f'微信API返回错误 - errcode: {wx_data.get("errcode")}, errmsg: {wx_data.get("errmsg")}')
            return make_err_response({}, f'微信API错误: {wx_data.get("errmsg", "未知错误")}')

        # 获取openid和session_key
        app.logger.info('正在从微信API响应中提取openid和session_key')
        openid = wx_data.get('openid')
        session_key = wx_data.get('session_key')

        app.logger.info(f'提取到的openid: {openid}')
        app.logger.info(f'提取到的session_key: {"*" * 10}')  # 隐藏session_key的实际值

        if not openid or not session_key:
            app.logger.error(
                f'微信API返回数据不完整 - openid存在: {bool(openid)}, session_key存在: {bool(session_key)}')
            return make_err_response({}, '微信API返回数据不完整')

        app.logger.info('成功获取openid和session_key，开始查询数据库中的用户信息')

        # 检查用户是否已存在
        existing_user = UserService.query_user_by_openid(openid)
        is_new = not bool(existing_user)
        app.logger.info(f'用户查询结果 - 是否为新用户: {is_new}, openid: {openid}')

        if not existing_user:
            app.logger.info('用户不存在，创建新用户...')
            # 创建新用户
            user_data = User(
                wechat_openid=openid,
                nickname=nickname,
                avatar_url=avatar_url,
                role=1,  # 默认为独居者角色
                status=1  # 默认为正常状态
            )
            created_user = UserService.create_user(user_data)
            app.logger.info(f'新用户创建成功，用户ID: {created_user.user_id}, openid: {openid}')

            # 使用返回的用户对象，不需要重新查询
            user = created_user

            # 自动分配到默认社区
            try:
                from wxcloudrun.community_service import CommunityService
                CommunityService.assign_user_to_community(user, DEFUALT_COMMUNITY_NAME)
                app.logger.info(f'新用户已自动分配到默认社区，用户ID: {user.user_id}')
            except Exception as e:
                app.logger.error(f'自动分配社区失败: {str(e)}', exc_info=True)
                # 不影响登录流程，只记录错误
        else:
            app.logger.info('用户已存在，检查是否需要更新用户信息...')
            # 更新现有用户信息（如果提供了新的头像或昵称）
            user = existing_user
            updated = False
            if nickname and user.nickname != nickname:
                app.logger.info(f'更新用户昵称: {user.nickname} -> {nickname}')
                user.nickname = nickname
                updated = True
            if avatar_url and user.avatar_url != avatar_url:
                app.logger.info(f'更新用户头像: {user.avatar_url} -> {avatar_url}')
                user.avatar_url = avatar_url
                updated = True
            if updated:
                app.logger.info('保存用户信息更新到数据库...')
                update_user_by_id(user)
                app.logger.info(f'用户信息更新成功，openid: {openid}')
            else:
                app.logger.info('用户信息无变化，无需更新')

        app.logger.info('开始生成JWT token和refresh token...')

        # 生成JWT token (access token)，设置2小时过期时间
        token_payload = {
            'openid': openid,
            'user_id': user.user_id,  # 添加用户ID到token中
            'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=2)  # 设置2小时过期时间
        }
        app.logger.info(f'JWT token payload: {token_payload}')

        # 从配置管理器获取TOKEN_SECRET确保编码和解码使用相同的密钥
        try:
            token_secret = get_token_secret()
        except ValueError as e:
            app.logger.error(f'获取TOKEN_SECRET失败: {str(e)}')
            return make_err_response({}, '服务器配置错误')
        app.logger.info(f'使用配置的TOKEN_SECRET: {token_secret[:20]}...')

        token = jwt.encode(token_payload, token_secret, algorithm='HS256')

        # 生成refresh token
        refresh_token = secrets.token_urlsafe(32)
        app.logger.info(f'生成的refresh_token: {refresh_token[:20]}...')

        # 设置refresh token过期时间为7天
        refresh_token_expire = datetime.datetime.now() + datetime.timedelta(days=7)

        # 更新用户信息，保存refresh token
        user.refresh_token = refresh_token
        user.refresh_token_expire = refresh_token_expire
        UserService.update_user_by_id(user)

        # 打印生成的token用于调试（只打印前50个字符）
        app.logger.info(f'生成的token前50字符: {token[:50]}...')
        app.logger.info(f'生成的token总长度: {len(token)}')

        app.logger.info('JWT token和refresh token生成成功')

    except Exception as e:
        app.logger.error(f'登录过程中发生未预期的错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'登录失败: {str(e)}')

    app.logger.info('登录流程完成，开始构造响应数据')

    # 构造返回数据，包含用户的 token、refresh token 和基本信息
    # 使用统一的响应格式
    response_data = _format_user_login_response(
        user, token, refresh_token, is_new_user=is_new
    )

    app.logger.info(f'返回的用户ID: {user.user_id}')
    app.logger.info(f'是否为新用户: {is_new}')
    app.logger.info(f'返回的token长度: {len(token)}')
    app.logger.info(f'返回的refresh_token长度: {len(refresh_token)}')
    app.logger.info('=== 登录接口执行完成 ===')

    # 返回自定义格式的响应
    return make_succ_response(response_data)


@app.route('/api/refresh_token', methods=['POST'])
def refresh_token():
    """
    刷新token接口，使用refresh token获取新的access token
    """
    app.logger.info('=== 开始执行刷新Token接口 ===')

    try:
        # 获取请求体参数
        params = request.get_json()
        if not params:
            app.logger.warning('刷新Token请求缺少请求体参数')
            return make_err_response({}, '缺少请求体参数')

        refresh_token = params.get('refresh_token')
        if not refresh_token:
            app.logger.warning('刷新Token请求缺少refresh_token参数')
            return make_err_response({}, '缺少refresh_token参数')

        app.logger.info('开始验证refresh token...')

        # 从数据库中查找用户信息
        from wxcloudrun.user_service import UserService
        user = UserService.query_user_by_refresh_token(refresh_token)
        if not user or not user.refresh_token or user.refresh_token != refresh_token:
            app.logger.warning(f'无效的refresh_token: {refresh_token[:20]}...')
            return make_err_response({}, '无效的refresh_token')

        # 检查refresh token是否过期
        if user.refresh_token_expire and user.refresh_token_expire < datetime.datetime.now():
            app.logger.warning(f'refresh_token已过期，用户ID: {user.user_id}')
            # 清除过期的refresh token
            user.refresh_token = None
            user.refresh_token_expire = None
            update_user_by_id(user)
            return make_err_response({}, 'refresh_token已过期')

        app.logger.info(f'找到用户，正在为用户ID: {user.user_id} 生成新token')

        # 生成新的JWT token（access token）
        token_payload = {
            'openid': user.wechat_openid,
            'user_id': user.user_id,
            'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=2)  # 设置2小时过期时间
        }
        try:
            token_secret = get_token_secret()
        except ValueError as e:
            app.logger.error(f'获取TOKEN_SECRET失败: {str(e)}')
            return make_err_response({}, '服务器配置错误')
        new_token = jwt.encode(token_payload, token_secret, algorithm='HS256')

        # 生成新的refresh token（可选：也可以继续使用现有的refresh token）
        new_refresh_token = secrets.token_urlsafe(32)
        # 设置新的refresh token过期时间（7天）
        new_refresh_token_expire = datetime.datetime.now() + datetime.timedelta(days=7)

        # 更新数据库中的refresh token
        user.refresh_token = new_refresh_token
        user.refresh_token_expire = new_refresh_token_expire
        update_user_by_id(user)

        app.logger.info(f'成功为用户ID: {user.user_id} 刷新token')

        response_data = {
            'token': new_token,
            'refresh_token': new_refresh_token,
            'expires_in': 7200  # 2小时（秒）
        }

        return make_succ_response(response_data)

    except jwt.PyJWTError as e:
        app.logger.error(f'JWT处理错误: {str(e)}')
        return make_err_response({}, f'JWT处理失败: {str(e)}')
    except Exception as e:
        app.logger.error(f'刷新Token过程中发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'刷新Token失败: {str(e)}')


@app.route('/api/logout', methods=['POST'])
def logout():
    """
    用户登出接口，清除refresh token
    """
    app.logger.info('=== 开始执行登出接口 ===')

    # 验证token
    from wxcloudrun.utils.auth import verify_token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    try:
        openid = decoded.get('openid')
        if not openid:
            return make_err_response({}, 'token无效')

        # 根据openid查找用户并清除refresh token
        user = query_user_by_openid(openid)
        if user:
            user.refresh_token = None
            user.refresh_token_expire = None
            update_user_by_id(user)
            app.logger.info(f'成功清除用户ID: {user.user_id} 的refresh token')

        return make_succ_response({'message': '登出成功'})

    except Exception as e:
        app.logger.error(f'登出过程中发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'登出失败: {str(e)}')


@app.route('/api/auth/register_phone', methods=['POST'])
def register_phone():
    from const_default import DEFUALT_COMMUNITY_NAME
    try:
        params = request.get_json() or {}
        phone = params.get('phone')
        code = params.get('code')
        nickname = params.get('nickname')
        avatar_url = params.get('avatar_url')
        password = params.get('password')
        if not phone or not code:
            return make_err_response({}, '缺少phone或code参数')

        # 标准化电话号码格式
        normalized_phone = normalize_phone_number(phone)

        if not _verify_sms_code(normalized_phone, 'register', code):
            return make_err_response({}, '验证码无效或已过期')
        if password:
            pwd = str(password)
            if len(pwd) < 8 or (not any(c.isalpha() for c in pwd)) or (not any(c.isdigit() for c in pwd)):
                return make_err_response({}, '密码强度不足')
        phone_secret = os.getenv('PHONE_ENC_SECRET', 'default_secret')
        phone_hash = sha256(
            f"{phone_secret}:{normalized_phone}".encode('utf-8')).hexdigest()
        existing = User.query.filter_by(phone_hash=phone_hash).first()

        # 严格按策略1：不验证密码，直接提示账号已存在
        if existing:
            app.logger.info(f'手机号已注册，提示用户直接登录: {phone}')
            return make_err_response({'code': 'PHONE_EXISTS'}, '该手机号已注册，请直接登录')

        # Create new user using UserService to avoid session issues
        from wxcloudrun.user_service import UserService
        # Generate masked phone number for display purposes only
        masked = normalized_phone[:3] + '****' + normalized_phone[-4:] if len(normalized_phone) >= 7 else normalized_phone
        app.logger.info(f"Creating user with masked phone: {masked} (phone_hash will be used for uniqueness)")
        nick = nickname or _gen_phone_nickname()

        # For phone users, create user with phone_number only (UserService will set wechat_openid to empty)
        user = User(phone_number=normalized_phone, nickname=nick, avatar_url=avatar_url, role=1, status=1)
        if password:
            user.password = password

        # Use UserService.create_user to properly handle sessions
        user = UserService.create_user(user)
        _audit(user.user_id, 'register_phone', {'phone': normalized_phone})

        # 自动分配到默认社区
        try:
            from wxcloudrun.community_service import CommunityService
            CommunityService.assign_user_to_community(user, DEFUALT_COMMUNITY_NAME)
            app.logger.info(f'手机注册用户已自动分配到默认社区，用户ID: {user.user_id}')
        except Exception as e:
            app.logger.error(f'手机注册用户自动分配社区失败: {str(e)}', exc_info=True)
            # 不影响注册流程，只记录错误

        token_payload = {'openid': user.wechat_openid, 'user_id': user.user_id,
                         'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=2)}
        try:
            token_secret = get_token_secret()
        except ValueError as e:
            app.logger.error(f'获取TOKEN_SECRET失败: {str(e)}')
            return make_err_response({}, '服务器配置错误')
        token = jwt.encode(token_payload, token_secret, algorithm='HS256')
        refresh_token = secrets.token_urlsafe(32)
        user.refresh_token = refresh_token
        user.refresh_token_expire = datetime.datetime.now() + datetime.timedelta(days=7)
        UserService.update_user_by_id(user)

        # 使用统一的响应格式
        response_data = _format_user_login_response(
            user, token, refresh_token, is_new_user=True
        )
        return make_succ_response(response_data)
    except Exception as e:
        app.logger.error(f'手机号注册失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'注册失败: {str(e)}')


@app.route('/api/auth/login_phone_code', methods=['POST'])
def login_phone_code():
    try:
        params = request.get_json() or {}
        phone = params.get('phone')
        code = params.get('code')
        if not phone or not code:
            return make_err_response({}, '缺少phone或code参数')

        # 标准化电话号码格式
        normalized_phone = normalize_phone_number(phone)

        if not _verify_sms_code(normalized_phone, 'login', code) and not _verify_sms_code(normalized_phone, 'register', code):
            return make_err_response({}, '验证码无效或已过期')
        phone_secret = os.getenv('PHONE_ENC_SECRET', 'default_secret')
        phone_hash = sha256(
            f"{phone_secret}:{normalized_phone}".encode('utf-8')).hexdigest()
        user = User.query.filter_by(phone_hash=phone_hash).first()
        if not user:
            return make_err_response({}, '用户不存在')
        if not user.nickname:
            user.nickname = _gen_phone_nickname()
            update_user_by_id(user)

        token_payload = {'openid': user.wechat_openid, 'user_id': user.user_id,
                         'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=2)}
        try:
            token_secret = get_token_secret()
        except ValueError as e:
            app.logger.error(f'获取TOKEN_SECRET失败: {str(e)}')
            return make_err_response({}, '服务器配置错误')
        token = jwt.encode(token_payload, token_secret, algorithm='HS256')
        refresh_token = secrets.token_urlsafe(32)
        user.refresh_token = refresh_token
        user.refresh_token_expire = datetime.datetime.now() + datetime.timedelta(days=7)
        update_user_by_id(user)
        _audit(user.user_id, 'login_phone_code', {'phone': phone})
        return make_succ_response({'token': token, 'refresh_token': refresh_token, 'user_id': user.user_id})
    except Exception as e:
        app.logger.error(f'验证码登录失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'登录失败: {str(e)}')


@app.route('/api/auth/login_phone_password', methods=['POST'])
def login_phone_password():
    try:
        params = request.get_json() or {}
        phone = params.get('phone')
        password = params.get('password')
        if not phone or not password:
            return make_err_response({}, '缺少phone或password参数')

        # 标准化电话号码格式
        normalized_phone = normalize_phone_number(phone)

        phone_secret = os.getenv('PHONE_ENC_SECRET', 'default_secret')
        phone_hash = sha256(
            f"{phone_secret}:{normalized_phone}".encode('utf-8')).hexdigest()
        user = User.query.filter_by(phone_hash=phone_hash).first()
        if not user:
            return make_err_response({'code': 'USER_NOT_FOUND'}, '账号不存在，请先注册')
        if not user.password_hash or not user.password_salt:
            return make_err_response({}, '账号未设置密码')
        pwd_hash = sha256(
            f"{password}:{user.password_salt}".encode('utf-8')).hexdigest()
        if pwd_hash != user.password_hash:
            return make_err_response({}, '密码不正确')
        if not user.nickname:
            user.nickname = _gen_phone_nickname()
            update_user_by_id(user)

        token_payload = {'openid': user.wechat_openid, 'user_id': user.user_id,
                         'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=2)}
        try:
            token_secret = get_token_secret()
        except ValueError as e:
            app.logger.error(f'获取TOKEN_SECRET失败: {str(e)}')
            return make_err_response({}, '服务器配置错误')
        token = jwt.encode(token_payload, token_secret, algorithm='HS256')
        refresh_token = secrets.token_urlsafe(32)
        user.refresh_token = refresh_token
        user.refresh_token_expire = datetime.datetime.now() + datetime.timedelta(days=7)
        update_user_by_id(user)
        _audit(user.user_id, 'login_phone_password', {'phone': phone})
        return make_succ_response({'token': token, 'refresh_token': refresh_token, 'user_id': user.user_id})
    except Exception as e:
        app.logger.error(f'密码登录失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'登录失败: {str(e)}')


@app.route('/api/auth/login_phone', methods=['POST'])
def login_phone():
    """
    手机号登录：需要同时验证验证码和密码
    """
    try:
        params = request.get_json() or {}
        phone = params.get('phone')
        code = params.get('code')
        password = params.get('password')

        # 参数验证
        if not phone or not code or not password:
            return make_err_response({}, '缺少phone、code或password参数')

        # 标准化电话号码格式
        normalized_phone = normalize_phone_number(phone)

        # 验证码验证（允许使用login或register类型的验证码）
        # 这样用户可以使用注册时发送的验证码进行登录
        if not _verify_sms_code(normalized_phone, 'login', code) and not _verify_sms_code(normalized_phone, 'register', code):
            return make_err_response({}, '验证码无效或已过期')

        # 查找用户
        phone_secret = os.getenv('PHONE_ENC_SECRET', 'default_secret')
        phone_hash = sha256(
            f"{phone_secret}:{normalized_phone}".encode('utf-8')).hexdigest()
        user = User.query.filter_by(phone_hash=phone_hash).first()

        if not user:
            return make_err_response({'code': 'USER_NOT_FOUND'}, '账号不存在，请先注册')
        if not user.password_hash or not user.password_salt:
            return make_err_response({}, '账号未设置密码')

        # 密码验证
        pwd_hash = sha256(
            f"{password}:{user.password_salt}".encode('utf-8')).hexdigest()
        if pwd_hash != user.password_hash:
            return make_err_response({}, '密码不正确')

        # 更新用户昵称（如果需要）
        if not user.nickname:
            user.nickname = _gen_phone_nickname()
            update_user_by_id(user)

        # 生成token
        token_payload = {'openid': user.wechat_openid, 'user_id': user.user_id,
                         'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=2)}
        try:
            token_secret = get_token_secret()
        except ValueError as e:
            app.logger.error(f'获取TOKEN_SECRET失败: {str(e)}')
            return make_err_response({}, '服务器配置错误')

        token = jwt.encode(token_payload, token_secret, algorithm='HS256')
        refresh_token = secrets.token_urlsafe(32)
        user.refresh_token = refresh_token
        user.refresh_token_expire = datetime.datetime.now() + datetime.timedelta(days=7)
        update_user_by_id(user)

        _audit(user.user_id, 'login_phone', {'phone': phone})

        # 使用统一的响应格式
        response_data = _format_user_login_response(
            user, token, refresh_token, is_new_user=False
        )
        return make_succ_response(response_data)

    except Exception as e:
        app.logger.error(f'手机号登录失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'登录失败: {str(e)}')