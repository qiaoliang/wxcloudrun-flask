


"""
认证模块路由
包含登录、注册、token管理等功能
"""

import logging
import datetime
import secrets
import jwt
import os
from hashlib import sha256
from flask import request, current_app
from . import auth_bp
from .services import _format_user_login_response
from app.shared import make_succ_response, make_err_response
from app.shared.utils.auth import generate_jwt_token, generate_refresh_token, verify_token
from wxcloudrun.user_service import UserService
from database.flask_models import User
from wxcloudrun.utils.validators import _verify_sms_code, _audit, _gen_phone_nickname, _hash_code, normalize_phone_number
from config_manager import get_token_secret
from const_default import DEFUALT_COMMUNITY_NAME

app_logger = logging.getLogger('log')


@auth_bp.route('/login_wechat', methods=['POST'])
def login_wechat():
    """
    微信登录接口，通过code获取用户信息并返回token
    :return: token
    """
    current_app.logger.info('=== 开始执行微信登录接口 ===')

    # 在日志中打印登录请求
    request_params = request.get_json()
    current_app.logger.info(f'login 请求参数: {request_params}')

    # 获取请求体参数
    params = request.get_json()
    if not params:
        current_app.logger.warning('登录请求缺少请求体参数')
        return make_err_response({}, '缺少请求体参数')

    current_app.logger.info('成功获取请求参数，开始检查code参数')

    code = params.get('code')
    if not code:
        current_app.logger.warning('登录请求缺少code参数')
        return make_err_response({}, '缺少code参数')

    # 打印code用于调试
    current_app.logger.info(f'获取到的code: {code}')

    # Layer 1: 入口点验证 - 支持可选的用户信息参数
    nickname = params.get('nickname')
    avatar_url = params.get('avatar_url')

    # Defense-in-depth: 记录参数接收情况但不强制要求
    current_app.logger.info(f'用户信息参数状态 - nickname存在: {bool(nickname)}, avatar_url存在: {bool(avatar_url)}')

    # 如果缺少用户信息，使用默认值但不阻止登录流程
    if not nickname or not avatar_url:
        current_app.logger.warning('登录请求缺少用户信息，将使用默认值继续处理')
        current_app.logger.info(f'请求参数详情: {params}')

        # 为缺失的参数提供默认值
        if not nickname:
            nickname = f"微信用户_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        if not avatar_url:
            avatar_url = "https://mmbiz.qpic.cn/mmbiz/icTdbqWNOwNRna42FI242Lcia07jQodd2FJGIYQfG0LAJGFxM4FbnQP6yfMxBgJ0F3YRqJCJ1aPAK2dQagdusBZg/0"

        current_app.logger.info(f'使用默认用户信息 - nickname: {nickname}, avatar_url默认头像')

    # Layer 1: 基础数据清理 - 截断过长的昵称
    if nickname and len(nickname.strip()) > 0:
        original_nickname = nickname.strip()
        if len(original_nickname) > 50:
            nickname = original_nickname[:50] + "..."
            current_app.logger.info(f'Layer 1: 昵称过长，截断处理: {original_nickname[40:50]}... -> {nickname[40:50]}...')
        else:
            nickname = original_nickname

    current_app.logger.info(
        f'最终使用的用户信息 - nickname: {nickname}, avatar_url: {avatar_url[:50]}...')

    current_app.logger.info('开始调用微信API获取用户openid和session_key')

    # 调用微信API获取用户信息
    try:
        # 使用新的微信API模块，根据环境变量智能选择真实或模拟API
        from wxcloudrun.wxchat_api import get_user_info_by_code
        current_app.logger.info('正在通过微信API模块获取用户信息...')
        wx_data = get_user_info_by_code(code)

        current_app.logger.info(f'微信API响应数据类型: {type(wx_data)}')
        current_app.logger.info(f'微信API响应内容: {wx_data}')

        # 检查微信API返回的错误
        if 'errcode' in wx_data:
            current_app.logger.error(
                f'微信API返回错误 - errcode: {wx_data.get("errcode")}, errmsg: {wx_data.get("errmsg")}')
            return make_err_response({}, f'微信API错误: {wx_data.get("errmsg", "未知错误")}')

        # 获取openid和session_key
        current_app.logger.info('正在从微信API响应中提取openid和session_key')
        openid = wx_data.get('openid')
        session_key = wx_data.get('session_key')

        current_app.logger.info(f'提取到的openid: {openid}')
        current_app.logger.info(f'提取到的session_key: {"*" * 10}')  # 隐藏session_key的实际值

        if not openid or not session_key:
            current_app.logger.error(
                f'微信API返回数据不完整 - openid存在: {bool(openid)}, session_key存在: {bool(session_key)}')
            return make_err_response({}, '微信API返回数据不完整')

        current_app.logger.info('成功获取openid和session_key，开始查询数据库中的用户信息')

        # 检查用户是否已存在
        existing_user = UserService.query_user_by_openid(openid)
        is_new = not bool(existing_user)
        current_app.logger.info(f'用户查询结果 - 是否为新用户: {is_new}, openid: {openid}')

        if not existing_user:
            current_app.logger.info('用户不存在，创建新用户...')

            # Layer 2: 业务逻辑验证 - 验证和清理用户数据
            try:
                # 验证昵称长度和内容
                if not nickname or len(nickname.strip()) == 0:
                    nickname = f"微信用户_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
                elif len(nickname) > 50:
                    nickname = nickname[:50] + "..."

                # 验证头像URL格式
                if not avatar_url or not avatar_url.startswith(('http://', 'https://')):
                    avatar_url = "https://mmbiz.qpic.cn/mmbiz/icTdbqWNOwNRna42FI242Lcia07jQodd2FJGIYQfG0LAJGFxM4FbnQP6yfMxBgJ0F3YRqJCJ1aPAK2dQagdusBZg/0"

                # 创建新用户
                user_data = User(
                    wechat_openid=openid,
                    nickname=nickname.strip(),
                    avatar_url=avatar_url.strip(),
                    role=1,  # 默认为独居者角色
                    status=1  # 默认为正常状态
                )
                created_user = UserService.create_user(user_data)
                current_app.logger.info(f'新用户创建成功，用户ID: {created_user.user_id}, openid: {openid}')

                # 使用返回的用户对象，不需要重新查询
                user = created_user

            except Exception as create_error:
                current_app.logger.error(f'创建用户时发生错误: {str(create_error)}')
                # 使用最小可用信息重试创建
                fallback_nickname = f"用户_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
                fallback_avatar = "https://mmbiz.qpic.cn/mmbiz/icTdbqWNOwNRna42FI242Lcia07jQodd2FJGIYQfG0LAJGFxM4FbnQP6yfMxBgJ0F3YRqJCJ1aPAK2dQagdusBZg/0"

                user_data = User(
                    wechat_openid=openid,
                    nickname=fallback_nickname,
                    avatar_url=fallback_avatar,
                    role=1,
                    status=1
                )
                created_user = UserService.create_user(user_data)
                user = created_user
                current_app.logger.warning(f'使用fallback信息创建用户成功，用户ID: {created_user.user_id}')

            # 自动分配到默认社区
            try:
                from wxcloudrun.community_service import CommunityService
                CommunityService.assign_user_to_community(user, DEFUALT_COMMUNITY_NAME)
                current_app.logger.info(f'新用户已自动分配到默认社区，用户ID: {user.user_id}')
            except Exception as e:
                current_app.logger.error(f'自动分配社区失败: {str(e)}', exc_info=True)
                # 不影响登录流程，只记录错误
        else:
            current_app.logger.info('用户已存在，检查是否需要更新用户信息...')
            # 更新现有用户信息（如果提供了新的头像或昵称）
            user = existing_user
            updated = False

            # Layer 3: 环境守卫 - 在更新操作前验证数据安全性
            try:
                # 验证昵称更新
                if nickname and user.nickname != nickname:
                    # 安全检查：防止恶意昵称，并进行截断处理
                    if len(nickname.strip()) > 0:
                        original_nickname = nickname.strip()
                        # Defense-in-depth: 截断过长的昵称
                        if len(original_nickname) > 50:
                            truncated_nickname = original_nickname[:50] + "..."
                            current_app.logger.info(f'昵称过长，截断处理: {original_nickname[:30]}... -> {truncated_nickname[:30]}...')
                            user.nickname = truncated_nickname
                        else:
                            user.nickname = original_nickname
                        updated = True
                    else:
                        current_app.logger.warning(f'昵称验证失败，跳过更新: {nickname}')

                # 验证头像URL更新
                if avatar_url and user.avatar_url != avatar_url:
                    # 安全检查：验证URL格式
                    if avatar_url.startswith(('http://', 'https://')) and len(avatar_url) <= 500:
                        current_app.logger.info(f'更新用户头像: {user.avatar_url[:30]}... -> {avatar_url[:30]}...')
                        user.avatar_url = avatar_url.strip()
                        updated = True
                    else:
                        current_app.logger.warning(f'头像URL验证失败，跳过更新: {avatar_url[:30]}...')

                # 检查并补充社区信息（修复历史遗留问题）
                if not user.community_id:
                    current_app.logger.info(f'用户无社区信息，自动分配到默认社区，用户ID: {user.user_id}')
                    try:
                        from wxcloudrun.community_service import CommunityService
                        CommunityService.assign_user_to_community(user, DEFUALT_COMMUNITY_NAME)
                        updated = True
                        current_app.logger.info(f'用户已成功分配到默认社区: {DEFUALT_COMMUNITY_NAME}')
                    except Exception as community_error:
                        current_app.logger.error(f'分配用户到默认社区失败: {str(community_error)}', exc_info=True)
                        # 不影响登录流程，只记录错误
                else:
                    current_app.logger.debug(f'用户已有社区信息，社区ID: {user.community_id}')

                # 执行更新操作
                if updated:
                    current_app.logger.info('保存用户信息更新到数据库...')
                    UserService.update_user_by_id(user)
                    current_app.logger.info(f'用户信息更新成功，openid: {openid}')
                else:
                    current_app.logger.info('用户信息无变化或验证未通过，无需更新')

            except Exception as update_error:
                current_app.logger.error(f'更新用户信息时发生错误: {str(update_error)}')
                # 不影响登录流程，只记录错误
                current_app.logger.info('继续登录流程，使用现有用户信息')

        current_app.logger.info('开始生成JWT token和refresh token...')

        token, error_response = generate_jwt_token(user, expires_hours=2)
        if error_response:
            return error_response

        # 使用工具函数生成refresh token
        refresh_token = generate_refresh_token(user, expires_days=7)

        # 保存refresh token到数据库
        UserService.update_user_by_id(user)

        # 打印生成的token用于调试（只打印前50个字符）
        current_app.logger.info(f'生成的token前50字符: {token[:50]}...')
        current_app.logger.info(f'生成的token总长度: {len(token)}')

        current_app.logger.info('JWT token和refresh token生成成功')

    except Exception as e:
        current_app.logger.error(f'登录过程中发生未预期的错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'登录失败: {str(e)}')

    # Layer 4: 调试仪表 - 增强日志记录和错误取证
    current_app.logger.info('登录流程完成，开始构造响应数据')

    # 记录详细的调试信息用于取证
    try:
        # 构造返回数据，包含用户的 token、refresh token 和基本信息
        response_data = _format_user_login_response(
            user, token, refresh_token, is_new_user=is_new
        )

        # 安全日志记录（不包含敏感信息）
        current_app.logger.info(f'微信登录成功 - 用户ID: {user.user_id}, 昵称: {user.nickname}, 新用户: {is_new}, 社区ID: {user.community_id}')

        # 验证响应数据完整性
        required_fields = ['token', 'refresh_token', 'user_id']
        missing_fields = [field for field in required_fields if not response_data.get(field)]
        if missing_fields:
            current_app.logger.error(f'响应数据缺少必需字段: {missing_fields}')
            raise Exception(f'响应数据不完整，缺少字段: {missing_fields}')

        current_app.logger.info('=== 微信登录接口执行完成 ===')

        # 返回自定义格式的响应
        return make_succ_response(response_data)

    except Exception as response_error:
        current_app.logger.error(f'构造响应数据时发生错误: {str(response_error)}')
        # 即使响应构造失败，也尝试返回最小可用响应
        try:
            minimal_response = {
                'token': token,
                'refresh_token': refresh_token,
                'user_id': user.user_id,
                'wechat_openid': user.wechat_openid,
                'nickname': user.nickname,
                'avatar_url': user.avatar_url,
                'phone_number': user.phone_number,
                'login_type': 'new_user' if is_new else 'existing_user'
            }
            current_app.logger.warning(f'使用最小响应格式返回，login_type: {minimal_response["login_type"]}')
            return make_succ_response(minimal_response)
        except Exception as fallback_error:
            current_app.logger.error(f'最小响应构造也失败: {str(fallback_error)}')
            return make_err_response({}, '登录成功但响应构造失败')


@auth_bp.route('/refresh_token', methods=['POST'])
def refresh_token():
    """
    刷新token接口，使用refresh token获取新的access token
    """
    current_app.logger.info('=== 开始执行刷新Token接口 ===')

    try:
        # 获取请求体参数
        params = request.get_json()
        if not params:
            current_app.logger.warning('刷新Token请求缺少请求体参数')
            return make_err_response({}, '缺少请求体参数')

        refresh_token = params.get('refresh_token')
        if not refresh_token:
            current_app.logger.warning('刷新Token请求缺少refresh_token参数')
            return make_err_response({}, '缺少refresh_token参数')

        current_app.logger.info(f'开始验证refresh token: {refresh_token[:20]}...')

        # 从数据库中查找用户信息
        user = UserService.query_user_by_refresh_token(refresh_token)
        
        # Add more debugging info
        if not user:
            current_app.logger.warning(f'未找到用户，refresh_token: {refresh_token[:20]}...')
            return make_err_response({}, '无效的refresh_token')
        
        current_app.logger.info(f'找到用户，用户ID: {user.user_id}')
        current_app.logger.info(f'数据库中存储的refresh_token: {user.refresh_token[:20] if user.refresh_token else None}...')
        current_app.logger.info(f'请求中的refresh_token: {refresh_token[:20]}...')
        current_app.logger.info(f'refresh_token匹配: {user.refresh_token == refresh_token}')
        current_app.logger.info(f'refresh_token字段存在: {bool(user.refresh_token)}')

        if not user.refresh_token or user.refresh_token != refresh_token:
            current_app.logger.warning(f'无效的refresh_token: {refresh_token[:20]}...')
            current_app.logger.warning(f'数据库中的token: {user.refresh_token[:20] if user.refresh_token else None}...')
            return make_err_response({}, '无效的refresh_token')

        # 检查refresh token是否过期
        if user.refresh_token_expire and user.refresh_token_expire < datetime.datetime.now():
            current_app.logger.warning(f'refresh_token已过期，用户ID: {user.user_id}')
            # 清除过期的refresh token
            user.refresh_token = None
            user.refresh_token_expire = None
            UserService.update_user_by_id(user)
            return make_err_response({}, 'refresh_token已过期')

        current_app.logger.info(f'找到用户，正在为用户ID: {user.user_id} 生成新token')

        # 使用工具函数生成新的JWT token
        new_token, error_response = generate_jwt_token(user, expires_hours=2)
        if error_response:
            return error_response

        # 使用工具函数生成新的refresh token
        new_refresh_token = generate_refresh_token(user, expires_days=7)

        # 保存到数据库
        UserService.update_user_by_id(user)

        current_app.logger.info(f'成功为用户ID: {user.user_id} 刷新token')

        response_data = {
            'token': new_token,
            'refresh_token': new_refresh_token,
            'expires_in': 7200  # 2小时（秒）
        }

        return make_succ_response(response_data)

    except jwt.PyJWTError as e:
        current_app.logger.error(f'JWT处理错误: {str(e)}')
        return make_err_response({}, f'JWT处理失败: {str(e)}')
    except Exception as e:
        current_app.logger.error(f'刷新Token过程中发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'刷新Token失败: {str(e)}')


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

    try:
        openid = decoded.get('openid')
        if not openid:
            return make_err_response({}, 'token无效')

        # 根据openid查找用户并清除refresh token
        user = UserService.query_user_by_openid(openid)
        if user:
            user.refresh_token = None
            user.refresh_token_expire = None
            UserService.update_user_by_id(user)
            current_app.logger.info(f'成功清除用户ID: {user.user_id} 的refresh token')

        return make_succ_response({'message': '登出成功'})

    except Exception as e:
        current_app.logger.error(f'登出过程中发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'登出失败: {str(e)}')


@auth_bp.route('/register_phone', methods=['POST'])
def register_phone():
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
        existing = UserService.query_user_by_phone_hash(phone_hash)

        # 严格按策略1：不验证密码，直接提示账号已存在
        if existing:
            current_app.logger.info(f'手机号已注册，提示用户直接登录: {phone}')
            return make_err_response({'code': 'PHONE_EXISTS'}, '该手机号已注册，请直接登录')

        # Create new user using UserService to avoid session issues
        # Generate masked phone number for display purposes only
        masked = normalized_phone[:3] + '****' + normalized_phone[-4:] if len(normalized_phone) >= 7 else normalized_phone
        current_app.logger.info(f"Creating user with masked phone: {masked} (phone_hash will be used for uniqueness)")
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
            current_app.logger.info(f'手机注册用户已自动分配到默认社区，用户ID: {user.user_id}')
        except Exception as e:
            current_app.logger.error(f'手机注册用户自动分配社区失败: {str(e)}', exc_info=True)
            # 不影响注册流程，只记录错误


        token, error_response = generate_jwt_token(user, expires_hours=2)
        if error_response:
            return error_response
        refresh_token = generate_refresh_token(user, expires_days=7)
        UserService.update_user_by_id(user)

        # 使用统一的响应格式
        response_data = _format_user_login_response(
            user, token, refresh_token, is_new_user=True
        )
        return make_succ_response(response_data)
    except Exception as e:
        current_app.logger.error(f'手机号注册失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'注册失败: {str(e)}')


@auth_bp.route('/login_phone_code', methods=['POST'])
def login_phone_code():
    current_app.logger.info('=== 开始执行手机号验证码登录接口 ===')
    try:
        params = request.get_json() or {}
        phone = params.get('phone')
        code = params.get('code')
        current_app.logger.info(f'登录请求参数 - phone: {phone}, code: {code}')
        
        if not phone or not code:
            current_app.logger.warning('登录请求缺少phone或code参数')
            return make_err_response({}, '缺少phone或code参数')

        # 标准化电话号码格式
        normalized_phone = normalize_phone_number(phone)
        current_app.logger.info(f'标准化后的手机号: {normalized_phone}')

        # 验证码验证 - 添加详细日志
        current_app.logger.info('开始验证SMS验证码...')
        login_valid = _verify_sms_code(normalized_phone, 'login', code)
        register_valid = _verify_sms_code(normalized_phone, 'register', code)
        current_app.logger.info(f'SMS验证结果 - login_valid: {login_valid}, register_valid: {register_valid}')
        
        if not login_valid and not register_valid:
            current_app.logger.warning(f'SMS验证码验证失败 - phone: {normalized_phone}, code: {code}')
            return make_err_response({}, '验证码无效或已过期')
        
        current_app.logger.info('SMS验证码验证通过，开始查询用户...')
        
        phone_secret = os.getenv('PHONE_ENC_SECRET', 'default_secret')
        phone_hash = sha256(
            f"{phone_secret}:{normalized_phone}".encode('utf-8')).hexdigest()
        current_app.logger.info(f'生成phone_hash: {phone_hash[:20]}...')
        
        # 数据库查询 - 添加执行时间监控
        import time
        
        try:
            current_app.logger.info('开始执行UserService.query_user_by_phone_hash...')
            start_time = time.time()
            user = UserService.query_user_by_phone_hash(phone_hash)
            query_time = time.time() - start_time
            current_app.logger.info(f'数据库查询完成，耗时: {query_time:.2f}秒，用户存在: {user is not None}')
            
            # 检查查询时间是否异常长
            if query_time > 3.0:
                current_app.logger.warning(f'数据库查询耗时过长: {query_time:.2f}秒')
                
        except Exception as db_error:
            current_app.logger.error(f'数据库查询异常: {str(db_error)}', exc_info=True)
            return make_err_response({}, '数据库查询失败')
            
        if not user:
            current_app.logger.warning(f'用户不存在 - phone: {normalized_phone}')
            return make_err_response({}, '用户不存在')
            
        current_app.logger.info(f'找到用户 - user_id: {user.user_id}, nickname: {user.nickname}')
        
        if not user.nickname:
            current_app.logger.info('用户昵称为空，生成默认昵称...')
            user.nickname = _gen_phone_nickname()
            UserService.update_user_by_id(user)
            current_app.logger.info(f'已更新用户昵称: {user.nickname}')

        current_app.logger.info('开始生成JWT token...')
        # 使用工具函数生成token
        token, error_response = generate_jwt_token(user, expires_hours=2)
        if error_response:
            return error_response
        refresh_token = generate_refresh_token(user, expires_days=7)
        
        current_app.logger.info('保存refresh token到数据库...')
        UserService.update_user_by_id(user)
        
        _audit(user.user_id, 'login_phone_code', {'phone': phone})
        current_app.logger.info('=== 手机号验证码登录接口执行完成 ===')
        
        return make_succ_response({'token': token, 'refresh_token': refresh_token, 'user_id': user.user_id})
    except Exception as e:
        current_app.logger.error(f'验证码登录失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'登录失败: {str(e)}')


@auth_bp.route('/login_phone_password', methods=['POST'])
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

        # 标准化电话号码格式
        normalized_phone = normalize_phone_number(phone)
        current_app.logger.info(f'标准化后的手机号: {normalized_phone}')

        phone_secret = os.getenv('PHONE_ENC_SECRET', 'default_secret')
        phone_hash = sha256(
            f"{phone_secret}:{normalized_phone}".encode('utf-8')).hexdigest()
        current_app.logger.info(f'生成phone_hash: {phone_hash[:20]}...')

        # 数据库查询 - 添加执行时间监控
        import time
        try:
            current_app.logger.info('开始执行UserService.query_user_by_phone_hash...')
            start_time = time.time()
            user = UserService.query_user_by_phone_hash(phone_hash)
            query_time = time.time() - start_time
            current_app.logger.info(f'数据库查询完成，耗时: {query_time:.2f}秒，用户存在: {user is not None}')
            
            # 检查查询时间是否异常长
            if query_time > 3.0:
                current_app.logger.warning(f'数据库查询耗时过长: {query_time:.2f}秒')
                
        except Exception as db_error:
            current_app.logger.error(f'数据库查询异常: {str(db_error)}', exc_info=True)
            return make_err_response({}, '数据库查询失败')

        if not user:
            current_app.logger.warning(f'用户不存在 - phone: {normalized_phone}')
            return make_err_response({'code': 'USER_NOT_FOUND'}, '账号不存在，请先注册')
        if not user.password_hash or not user.password_salt:
            current_app.logger.warning(f'用户未设置密码 - user_id: {user.user_id}')
            return make_err_response({}, '账号未设置密码')
        pwd_hash = sha256(
            f"{password}:{user.password_salt}".encode('utf-8')).hexdigest()
        if pwd_hash != user.password_hash:
            current_app.logger.warning(f'密码验证失败 - user_id: {user.user_id}')
            return make_err_response({}, '密码不正确')
        
        current_app.logger.info(f'密码验证成功，开始处理用户信息 - user_id: {user.user_id}')
        if not user.nickname:
            user.nickname = _gen_phone_nickname()
            UserService.update_user_by_id(user)
            current_app.logger.info(f'已更新用户昵称: {user.nickname}')

        current_app.logger.info('开始生成JWT token...')
        # 使用工具函数生成token
        token, error_response = generate_jwt_token(user, expires_hours=2)
        if error_response:
            return error_response
        refresh_token = generate_refresh_token(user, expires_days=7)
        
        current_app.logger.info('保存refresh token到数据库...')
        UserService.update_user_by_id(user)
        _audit(user.user_id, 'login_phone_password', {'phone': phone})
        
        current_app.logger.info('=== 手机号密码登录接口执行完成 ===')
        return make_succ_response({'token': token, 'refresh_token': refresh_token, 'user_id': user.user_id})
    except Exception as e:
        current_app.logger.error(f'密码登录失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'登录失败: {str(e)}')


@auth_bp.route('/login_phone', methods=['POST'])
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

        # 标准化电话号码格式
        normalized_phone = normalize_phone_number(phone)
        current_app.logger.info(f'标准化后的手机号: {normalized_phone}')

        # 验证码验证（允许使用login或register类型的验证码）
        # 这样用户可以使用注册时发送的验证码进行登录
        current_app.logger.info('开始验证SMS验证码...')
        code_valid = _verify_sms_code(normalized_phone, 'login', code) or _verify_sms_code(normalized_phone, 'register', code)
        if not code_valid:
            current_app.logger.warning(f'验证码验证失败 - phone: {normalized_phone}, code: {code}')
            return make_err_response({}, '验证码无效或已过期')
        current_app.logger.info('验证码验证通过')

        # 查找用户
        phone_secret = os.getenv('PHONE_ENC_SECRET', 'default_secret')
        phone_hash = sha256(
            f"{phone_secret}:{normalized_phone}".encode('utf-8')).hexdigest()
        current_app.logger.info(f'生成phone_hash: {phone_hash[:20]}...')

        # 数据库查询 - 添加执行时间监控
        import time
        try:
            current_app.logger.info('开始执行UserService.query_user_by_phone_hash...')
            start_time = time.time()
            user = UserService.query_user_by_phone_hash(phone_hash)
            query_time = time.time() - start_time
            current_app.logger.info(f'数据库查询完成，耗时: {query_time:.2f}秒，用户存在: {user is not None}')
            
            # 检查查询时间是否异常长
            if query_time > 3.0:
                current_app.logger.warning(f'数据库查询耗时过长: {query_time:.2f}秒')
                
        except Exception as db_error:
            current_app.logger.error(f'数据库查询异常: {str(db_error)}', exc_info=True)
            return make_err_response({}, '数据库查询失败')

        if not user:
            current_app.logger.warning(f'用户不存在 - phone: {normalized_phone}')
            return make_err_response({'code': 'USER_NOT_FOUND'}, '账号不存在，请先注册')
        if not user.password_hash or not user.password_salt:
            current_app.logger.warning(f'用户未设置密码 - user_id: {user.user_id}')
            return make_err_response({}, '账号未设置密码')

        # 验证密码
        pwd_hash = sha256(
            f"{password}:{user.password_salt}".encode('utf-8')).hexdigest()
        if pwd_hash != user.password_hash:
            current_app.logger.warning(f'密码验证失败 - user_id: {user.user_id}')
            return make_err_response({}, '密码不正确')
        
        current_app.logger.info(f'密码验证成功，开始处理用户信息 - user_id: {user.user_id}')
        if not user.nickname:
            user.nickname = _gen_phone_nickname()
            UserService.update_user_by_id(user)
            current_app.logger.info(f'已更新用户昵称: {user.nickname}')

        current_app.logger.info('开始生成JWT token...')
        # 使用工具函数生成token
        token, error_response = generate_jwt_token(user, expires_hours=2)
        if error_response:
            return error_response
        refresh_token = generate_refresh_token(user, expires_days=7)
        
        current_app.logger.info('保存refresh token到数据库...')
        UserService.update_user_by_id(user)
        _audit(user.user_id, 'login_phone', {'phone': phone})
        
        current_app.logger.info('=== 手机号登录接口执行完成 ===')
        return make_succ_response({'token': token, 'refresh_token': refresh_token, 'user_id': user.user_id})
    except Exception as e:
        current_app.logger.error(f'手机号登录失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'登录失败: {str(e)}')