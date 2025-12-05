from sqlalchemy import text
import logging
from flask import Flask, render_template, request, Response
from flask_cors import CORS
import json
import time
from datetime import datetime, date, timedelta, time
import secrets
import jwt
import requests
from functools import wraps
from dotenv import load_dotenv  # 添加缺失的导入
from wxcloudrun import db, app  # 从wxcloudrun导入app对象
from wxcloudrun.model import User, Counters, CheckinRule, CheckinRecord, SupervisionRuleRelation
from wxcloudrun.response import make_succ_empty_response, make_succ_response, make_err_response
from wxcloudrun.dao import *
from wxcloudrun.model import ShareLink, ShareLinkAccessLog
from wxcloudrun.model import VerificationCode, UserAuditLog
from wxcloudrun.sms_service import create_sms_provider, generate_code
from hashlib import sha256
import os
import secrets
from config_manager import get_token_secret, get_wechat_config, analyze_all_configs, detect_external_systems_status

# 加载环境变量
load_dotenv()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        decoded, error_response = verify_token()
        if error_response:
            return error_response
        return f(decoded, *args, **kwargs)
    return decorated_function


@app.route('/')
def index():
    """
    :return: 返回index页面
    """
    app.logger.info("主页访问")
    return render_template('index.html')


@app.route('/env')
def env_viewer():
    """
    :return: 返回环境配置查看器页面
    """
    app.logger.info("环境配置查看器页面访问")
    try:
        with open('static/env_viewer.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "环境配置查看器页面未找到", 404


@app.route('/api/count', methods=['POST'])
def count():
    """
    :return:计数结果/清除结果
    """

    # 获取请求体参数
    params = request.get_json()
    app.logger.info(f"接收到计数器POST请求，参数: {params}")

    # 检查action参数
    if 'action' not in params:
        app.logger.warning("请求中缺少action参数")
        return make_err_response('缺少action参数')

    # 按照不同的action的值，进行不同的操作
    action = params['action']
    app.logger.info(f"执行操作: {action}")

    # 执行自增操作
    if action == 'inc':
        app.logger.info("开始执行计数器自增操作")
        counter = query_counterbyid(1)
        app.logger.info(f"查询到的计数器: {counter.count if counter else 'None'}")

        if counter is None:
            app.logger.info("计数器不存在，创建新的计数器，值设为1")
            counter = Counters()
            counter.id = 1
            counter.count = 1
            counter.created_at = datetime.now()
            counter.updated_at = datetime.now()
            insert_counter(counter)
            app.logger.info("新计数器已插入数据库")
        else:
            app.logger.info(f"计数器存在，当前值: {counter.count}，即将递增")
            counter.count += 1
            app.logger.info(f"递增后值: {counter.count}")
            counter.updated_at = datetime.now()
            update_counterbyid(counter)
            app.logger.info("计数器已更新")

        app.logger.info(f"返回计数值: {counter.count}")
        return make_succ_response(counter.count)

    # 执行清0操作
    elif action == 'clear':
        app.logger.info("执行清零操作")
        delete_counterbyid(1)
        app.logger.info("计数器已清零")
        return make_succ_empty_response()

    # action参数错误
    else:
        app.logger.warning(f"无效的action参数: {action}")
        return make_err_response('action参数错误')


@app.route('/api/count', methods=['GET'])
def get_count():
    """
    :return: 计数的值
    """
    app.logger.info("接收到计数器GET请求")
    counter = query_counterbyid(1)
    count_value = 0 if counter is None else counter.count
    app.logger.info(f"查询到的计数器值: {count_value}")
    return make_succ_response(count_value)


@app.route('/api/get_envs', methods=['GET'])
def get_envs():
    """
    获取环境配置信息
    :return: 环境配置详细信息（支持JSON和TOML格式）
    """
    app.logger.info("接收到环境配置GET请求")

    try:
        # 获取配置分析结果
        config_analysis = analyze_all_configs()

        # 获取外部系统状态
        external_systems = detect_external_systems_status()

        # 检查请求的格式
        accept_header = request.headers.get('Accept', '')
        format_param = request.args.get('format', '').lower()

        # 如果请求text/plain或format=txt，返回TOML格式
        if 'text/plain' in accept_header or format_param == 'txt' or format_param == 'toml':
            return _format_envs_as_toml(config_analysis, external_systems)

        # 默认返回JSON格式
        response_data = {
            **config_analysis,
            'timestamp': datetime.now().isoformat() + 'Z',
            'external_systems': external_systems
        }

        app.logger.info("成功获取环境配置信息")
        return make_succ_response(response_data)

    except Exception as e:
        app.logger.error(f"获取环境配置信息失败: {str(e)}")
        return make_err_response(f"获取环境配置信息失败: {str(e)}")


def _format_envs_as_toml(config_analysis, external_systems):
    """
    将环境配置信息格式化为TOML风格的文本格式
    """
    lines = []

    # 添加头部信息
    lines.append("# 安全守护应用环境配置信息")
    lines.append(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # 基础信息
    lines.append("[基础信息]")
    lines.append(f"环境类型 = \"{config_analysis['environment']}\"")
    lines.append(f"配置文件 = \"{config_analysis['config_source']}\"")
    lines.append("")

    # 环境变量
    lines.append("[环境变量]")
    variables = config_analysis['variables']

    # 按名称排序
    for var_name in sorted(variables.keys()):
        var_info = variables[var_name]
        value = var_info['effective_value']
        data_type = var_info['data_type']

        # 根据数据类型格式化值
        if data_type == 'null' or value == '':
            formatted_value = 'null'
        elif data_type == 'boolean':
            formatted_value = value.lower() if value.lower() in [
                'true', 'false'] else value
        elif data_type in ['integer', 'float']:
            formatted_value = value
        else:
            # 字符串类型需要加引号
            formatted_value = f'"{value}"'

        # 添加注释信息
        comment = f"  # 数据类型: {data_type}"
        if var_info['is_sensitive']:
            comment += " [敏感信息]"

        lines.append(f"{var_name} = {formatted_value}{comment}")

    lines.append("")

    # 外部系统状态
    lines.append("[外部系统状态]")
    for system_name, system_info in external_systems.items():
        lines.append(f"# {system_info['name']}")
        lines.append(f"{system_name}.is_mock = {system_info['is_mock']}")
        lines.append(f"{system_name}.status = \"{system_info['status']}\"")

        # 添加配置信息
        if 'config' in system_info:
            lines.append(f"{system_name}.配置 = {{")
            for key, value in system_info['config'].items():
                if value is None:
                    formatted_value = 'null'
                elif isinstance(value, bool):
                    formatted_value = str(value).lower()
                elif isinstance(value, (int, float)):
                    formatted_value = str(value)
                else:
                    formatted_value = f'"{value}"'
                lines.append(f"  {key} = {formatted_value}")
            lines.append("}")
        lines.append("")

    # 添加结尾
    lines.append("# 配置信息结束")

    toml_content = "\n".join(lines)
    return Response(toml_content, mimetype='text/plain; charset=utf-8')


@app.route('/api/login', methods=['POST'])
def login():
    """
    登录接口，通过code获取用户信息并返回token
    :return: token
    """
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

    # 获取可能传递的用户信息
    nickname = params.get('nickname')
    avatar_url = params.get('avatar_url')

    app.logger.info(
        f'获取到的用户信息 - nickname: {nickname}, avatar_url: {avatar_url}')

    app.logger.info('开始调用微信API获取用户openid和session_key')

    # 调用微信API获取用户信息
    try:
        # 使用新的微信API模块，根据环境变量智能选择真实或模拟API
        from .wxchat_api import get_user_info_by_code

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
        existing_user = query_user_by_openid(openid)
        is_new = not bool(existing_user)
        app.logger.info(f'用户查询结果 - 是否为新用户: {is_new}, openid: {openid}')

        if not existing_user:
            app.logger.info('用户不存在，创建新用户...')
            # 创建新用户
            user = User(
                wechat_openid=openid,
                nickname=nickname,
                avatar_url=avatar_url,
                role=1,  # 默认为独居者角色
                status=1  # 默认为正常状态
            )
            insert_user(user)
            app.logger.info(f'新用户创建成功，用户ID: {user.user_id}, openid: {openid}')
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

        import datetime
        import secrets

        # 生成JWT token (access token)，设置2小时过期时间
        token_payload = {
            'openid': openid,
            'user_id': user.user_id,  # 添加用户ID到token中
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2)  # 设置2小时过期时间
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
        update_user_by_id(user)

        # 打印生成的token用于调试（只打印前50个字符）
        app.logger.info(f'生成的token前50字符: {token[:50]}...')
        app.logger.info(f'生成的token总长度: {len(token)}')

        app.logger.info('JWT token和refresh token生成成功')

    except Exception as e:
        app.logger.error(f'登录过程中发生未预期的错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'登录失败: {str(e)}')

    app.logger.info('登录流程完成，开始构造响应数据')

    # 构造返回数据，包含用户的 token 和 refresh token
    response_data = {
        'token': token,
        'refresh_token': refresh_token,  # 添加refresh token
        'user_id': user.user_id,
        'is_new_user': is_new,  # 标识是否为新用户
        'expires_in': 7200  # 2小时（秒）
    }

    app.logger.info(f'返回的用户ID: {user.user_id}')
    app.logger.info(f'是否为新用户: {is_new}')
    app.logger.info(f'返回的token长度: {len(token)}')
    app.logger.info(f'返回的refresh_token长度: {len(refresh_token)}')
    app.logger.info('=== 登录接口执行完成 ===')

    # 返回自定义格式的响应
    return make_succ_response(response_data)


@app.route('/api/user/profile', methods=['GET', 'POST'])
def user_profile():
    """
    用户信息接口，支持获取和更新用户信息
    GET: 获取用户信息
    POST: 更新用户信息
    """
    app.logger.info('=== 开始执行用户信息接口 ===')
    app.logger.info(f'请求方法: {request.method}')
    app.logger.info(f'请求头信息: {dict(request.headers)}')
    app.logger.info('准备获取请求体参数...')

    # 获取请求体参数 - 对于GET请求，通常没有请求体
    try:
        if request.method in ['POST', 'PUT', 'PATCH']:  # 只对有请求体的方法获取JSON
            params = request.get_json() if request.is_json else {}
        else:
            params = {}  # GET请求通常没有请求体
    except Exception as e:
        app.logger.warning(f'解析请求JSON失败: {str(e)}')
        params = {}
    app.logger.info(f'请求体参数: {params}')

    # 验证token
    auth_header = request.headers.get('Authorization', '')
    app.logger.info(f'原始Authorization头: {auth_header}')
    if auth_header.startswith('Bearer '):
        header_token = auth_header[7:]  # 去掉 'Bearer ' 前缀
        app.logger.info(f'去掉Bearer前缀后的token: {header_token}')
    else:
        header_token = auth_header
        app.logger.info(f'未找到Bearer前缀，直接使用Authorization头: {header_token}')
    token = params.get('token') or header_token

    app.logger.info(f'最终使用的token: {token}')

    # 打印传入的token用于调试
    app.logger.info(f'从请求中获取的token: {token}')
    app.logger.info(f'Authorization header完整内容: {auth_header}')

    if not token:
        app.logger.warning('请求中缺少token参数')
        return make_err_response({}, '缺少token参数')

    try:
        app.logger.info(f'开始处理token解码，原始token: {token}')
        # 解码token
        # 检查token是否包含额外的引号并去除
        if token and token.startswith('"') and token.endswith('"'):
            app.logger.info('检测到token包含额外引号，正在去除...')
            token = token[1:-1]  # 去除首尾的引号
            app.logger.info(f'去除引号后的token: {token[:50]}...')
        else:
            app.logger.info(f'token不包含额外引号或为空，无需处理')

        # 从配置管理器获取TOKEN_SECRET确保编码和解码使用相同的密钥
        try:
            token_secret = get_token_secret()
        except ValueError as e:
            app.logger.error(f'获取TOKEN_SECRET失败: {str(e)}')
            return make_err_response({}, '服务器配置错误')

        app.logger.info(
            f'用于解码的TOKEN_SECRET: {token_secret[:20]}...')  # 只显示前20个字符
        app.logger.info(f'准备解码token: {token[:50]}...')

        # 解码token，启用过期验证
        decoded = jwt.decode(
            token,
            token_secret,
            algorithms=['HS256']
        )
        app.logger.info(f'JWT解码成功，解码后的payload: {decoded}')
        openid = decoded.get('openid')
        app.logger.info(f'从解码结果中获取的openid: {openid}')

        if not openid:
            app.logger.error('解码后的token中未找到openid')
            return make_err_response({}, 'token无效')

        # 根据HTTP方法决定操作
        if request.method == 'GET':
            app.logger.info(f'处理GET请求 - 查询用户信息，openid: {openid}')
            # 查询用户信息
            user = query_user_by_openid(openid)
            app.logger.info(f'查询到的用户: {user}')
            if not user:
                app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
                return make_err_response({}, '用户不存在')

            # 返回用户信息
            user_data = {
                'user_id': user.user_id,
                'wechat_openid': user.wechat_openid,
                'phone_number': user.phone_number,
                'nickname': user.nickname,
                'avatar_url': user.avatar_url,
                'role': user.role_name,  # 返回字符串形式的角色名
                'community_id': user.community_id,
                'status': user.status_name,  # 返回字符串形式的状态名
                'is_solo_user': getattr(user, 'is_solo_user', True),
                'is_supervisor': getattr(user, 'is_supervisor', False),
                'is_community_worker': getattr(user, 'is_community_worker', False)
            }

            app.logger.info(f'成功查询到用户信息，用户ID: {user.user_id}，准备返回响应')
            return make_succ_response(user_data)

        elif request.method == 'POST':
            app.logger.info(f'POST请求 - 更新用户信息，openid: {openid}')
            # 查询用户
            user = query_user_by_openid(openid)
            if not user:
                app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
                return make_err_response({}, '用户不存在')

            # 获取可更新的用户信息（只更新非空字段）
            nickname = params.get('nickname')
            avatar_url = params.get('avatar_url')
            phone_number = params.get('phone_number')
            role = params.get('role')
            community_id = params.get('community_id')
            status = params.get('status')
            # 权限组合字段
            is_solo_user = params.get('is_solo_user')
            is_supervisor = params.get('is_supervisor')
            is_community_worker = params.get('is_community_worker')

            app.logger.info(
                f'待更新的用户信息 - nickname: {nickname}, avatar_url: {avatar_url}, phone_number: {phone_number}, role: {role}')

            # 更新用户信息到数据库
            if nickname is not None:
                app.logger.info(f'更新nickname: {user.nickname} -> {nickname}')
                user.nickname = nickname
            if avatar_url is not None:
                app.logger.info(
                    f'更新avatar_url: {user.avatar_url} -> {avatar_url}')
                user.avatar_url = avatar_url
            if phone_number is not None:
                app.logger.info(
                    f'更新phone_number: {user.phone_number} -> {phone_number}')
                user.phone_number = phone_number
            if role is not None:
                app.logger.info(f'更新role: {user.role} -> {role}')
                # 如果传入的是字符串，转换为对应的整数值
                if isinstance(role, str):
                    role_value = User.get_role_value(role)
                    if role_value is not None:
                        user.role = role_value
                elif isinstance(role, int):
                    user.role = role
            # 更新权限组合字段
            if is_solo_user is not None:
                app.logger.info(
                    f'更新is_solo_user: {user.is_solo_user} -> {is_solo_user}')
                user.is_solo_user = bool(is_solo_user)
            if is_supervisor is not None:
                app.logger.info(
                    f'更新is_supervisor: {user.is_supervisor} -> {is_supervisor}')
                user.is_supervisor = bool(is_supervisor)
            if is_community_worker is not None:
                app.logger.info(
                    f'更新is_community_worker: {user.is_community_worker} -> {is_community_worker}')
                user.is_community_worker = bool(is_community_worker)
            if community_id is not None:
                app.logger.info(
                    f'更新community_id: {user.community_id} -> {community_id}')
                user.community_id = community_id
            if status is not None:
                app.logger.info(f'更新status: {user.status} -> {status}')
                # 如果传入的是字符串，转换为对应的整数值
                if isinstance(status, str):
                    status_value = User.get_status_value(status)
                    if status_value is not None:
                        user.status = status_value
                elif isinstance(status, int):
                    user.status = status
            user.updated_at = datetime.now()

            # 保存到数据库
            update_user_by_id(user)

            app.logger.info(f'用户 {openid} 信息更新成功')

            return make_succ_response({'message': '用户信息更新成功'})
        else:
            # 处理不支持的HTTP方法
            app.logger.warning(f'不支持的HTTP方法: {request.method}')
            return make_err_response({}, f'不支持的HTTP方法: {request.method}')

    except jwt.ExpiredSignatureError as e:
        app.logger.error(f'token已过期: {str(e)}')
        return make_err_response({}, 'token已过期')
    except jwt.InvalidSignatureError as e:
        error_subclass = type(e).__name__
        app.logger.error(f"❌  InvalidSignatureError 实际异常子类：{error_subclass}")
        app.logger.error(f"InvalidSignatureError 详细描述：{str(e)}")
        app.logger.error(f'token签名验证失败: {str(e)}')
        app.logger.error('可能原因：TOKEN_SECRET配置不一致、token被篡改或格式错误')
        return make_err_response({}, 'token签名无效')
    except jwt.DecodeError as e:
        # 捕获更详细的 DecodeError 的子类错误，打印详细信息
        # 关键代码：获取实际子类名称
        error_subclass = type(e).__name__
        app.logger.error(f"❌ 实际异常子类：{error_subclass}")
        app.logger.error(f"详细描述：{str(e)}")

        app.logger.error(f'token解码失败: {str(e)}')
        app.logger.error('可能原因：token格式错误（非标准JWT格式）、token被截断或包含非法字符')
        # 额外调试信息
        app.logger.info(f'尝试解析的token长度: {len(token) if token else 0}')
        if token:
            token_parts = token.split('.')
            app.logger.info(f'token段数: {len(token_parts)}')
            if len(token_parts) >= 2:
                import base64
                try:
                    # 尝试解码header部分查看格式
                    header_part = token_parts[0]
                    # 补齐Base64 padding
                    missing_padding = len(header_part) % 4
                    if missing_padding:
                        header_part += '=' * (4 - missing_padding)
                    header_decoded = base64.urlsafe_b64decode(header_part)
                    app.logger.info(
                        f'token header解码成功: {header_decoded.decode("utf-8")}')
                except Exception as decode_err:
                    app.logger.error(f'token header解码失败: {str(decode_err)}')
        return make_err_response({}, 'token格式错误')
    except jwt.InvalidTokenError as e:
        app.logger.error(f'token无效: {str(e)}')
        return make_err_response({}, 'token无效')
    except Exception as e:
        app.logger.error(f'处理用户信息时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'处理用户信息失败: {str(e)}')

    app.logger.info('=== 用户信息接口执行完成 ===')


@app.route('/api/users/search', methods=['GET'])
@login_required
def search_users(decoded):
    """
    根据昵称关键词搜索用户（排除自己），默认返回最多10条
    参数：nickname（关键词），limit（可选，默认10）
    """
    try:
        params = request.args
        keyword = params.get('nickname', '').strip()
        limit = int(params.get('limit', 10))

        if not keyword or len(keyword) < 1:
            return make_succ_response({'users': []})

        # 当前用户
        openid = decoded.get('openid')
        current_user = query_user_by_openid(openid)
        if not current_user:
            return make_err_response({}, '用户不存在')

        # 搜索
        users = User.query.filter(
            User.nickname.ilike(f'%{keyword}%'),
            User.user_id != current_user.user_id
        ).order_by(User.updated_at.desc()).limit(limit).all()

        result = []
        for u in users:
            # 计算是否具备监护能力（已有任意已批准监督关系，或者标记为is_supervisor）
            is_supervisor_flag = getattr(u, 'is_supervisor', False)
            if not is_supervisor_flag:
                rel_exists = SupervisionRuleRelation.query.filter(
                    SupervisionRuleRelation.supervisor_user_id == u.user_id,
                    SupervisionRuleRelation.status == 2
                ).first()
                is_supervisor_flag = rel_exists is not None

            result.append({
                'user_id': u.user_id,
                'nickname': u.nickname,
                'avatar_url': u.avatar_url,
                'is_supervisor': is_supervisor_flag
            })

        return make_succ_response({'users': result})
    except Exception as e:
        app.logger.error(f'搜索用户失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'搜索用户失败: {str(e)}')

# 辅助函数：验证JWT token


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


def _hash_code(phone, code, salt):
    return sha256(f"{phone}:{code}:{salt}".encode('utf-8')).hexdigest()


def _code_expiry_minutes():
    try:
        return int(os.getenv('CONFIG_VERIFICATION_CODE_EXPIRY', '5'))
    except Exception:
        return 5


def _gen_phone_nickname():
    s = 'phone_' + secrets.token_hex(8)
    return s[:100]


@app.route('/api/sms/send_code', methods=['POST'])
def sms_send_code():
    try:
        params = request.get_json() or {}
        phone = params.get('phone')
        purpose = params.get('purpose', 'register')
        if not phone:
            return make_err_response({}, '缺少phone参数')
        now = datetime.now()
        vc = VerificationCode.query.filter_by(
            phone_number=phone, purpose=purpose).first()
        if vc and (now - vc.last_sent_at).total_seconds() < 60:
            return make_err_response({}, '请求过于频繁，请稍后再试')
        code = generate_code(6)
        salt = secrets.token_hex(8)
        code_hash = _hash_code(phone, code, salt)
        expires_at = now + timedelta(minutes=_code_expiry_minutes())
        if not vc:
            vc = VerificationCode(phone_number=phone, purpose=purpose, code_hash=code_hash,
                                  salt=salt, expires_at=expires_at, last_sent_at=now)
            db.session.add(vc)
        else:
            vc.code_hash = code_hash
            vc.salt = salt
            vc.expires_at = expires_at
            vc.last_sent_at = now
        db.session.commit()
        provider = create_sms_provider()
        provider.send(phone, f"验证码: {code}，{_code_expiry_minutes()}分钟内有效")
        resp = {'message': '验证码已发送'}
        debug_flag = os.getenv('SMS_DEBUG_RETURN_CODE', '0') == '1' or request.headers.get(
            'X-Debug-Code') == '1'
        if debug_flag:
            resp['debug_code'] = code
        return make_succ_response(resp)
    except Exception as e:
        app.logger.error(f'发送验证码失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'发送验证码失败: {str(e)}')


def _verify_sms_code(phone, purpose, code):
    vc = VerificationCode.query.filter_by(
        phone_number=phone, purpose=purpose).first()
    if not vc:
        return False
    if vc.expires_at < datetime.now():
        return False
    return vc.code_hash == _hash_code(phone, code, vc.salt)


def _audit(user_id, action, detail=None):
    try:
        log = UserAuditLog(user_id=user_id, action=action, detail=json.dumps(
            detail) if isinstance(detail, dict) else detail)
        db.session.add(log)
        db.session.commit()
    except Exception:
        pass


@app.route('/api/auth/register_phone', methods=['POST'])
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
        if not _verify_sms_code(phone, 'register', code):
            return make_err_response({}, '验证码无效或已过期')
        if password:
            pwd = str(password)
            if len(pwd) < 8 or (not any(c.isalpha() for c in pwd)) or (not any(c.isdigit() for c in pwd)):
                return make_err_response({}, '密码强度不足')
        phone_secret = os.getenv('PHONE_ENC_SECRET', 'default_secret')
        phone_hash = sha256(
            f"{phone_secret}:{phone}".encode('utf-8')).hexdigest()
        existing = User.query.filter_by(phone_hash=phone_hash).first()
        if existing:
            return make_err_response({}, '手机号已注册')
        salt = secrets.token_hex(8)
        pwd_hash = sha256(f"{password or ''}:{salt}".encode(
            'utf-8')).hexdigest() if password else None
        masked = phone[:3] + '****' + phone[-4:] if len(phone) >= 7 else phone
        nick = nickname or _gen_phone_nickname()
        user = User(wechat_openid=f"phone_{phone}", phone_number=masked, phone_hash=phone_hash, password_hash=pwd_hash,
                    password_salt=salt if password else None, nickname=nick, avatar_url=avatar_url, role=1, status=1)
        insert_user(user)
        _audit(user.user_id, 'register_phone', {'phone': phone})
        import datetime as dt
        token_payload = {'openid': user.wechat_openid, 'user_id': user.user_id,
                         'exp': dt.datetime.utcnow() + dt.timedelta(hours=2)}
        try:
            token_secret = get_token_secret()
        except ValueError as e:
            app.logger.error(f'获取TOKEN_SECRET失败: {str(e)}')
            return make_err_response({}, '服务器配置错误')
        token = jwt.encode(token_payload, token_secret, algorithm='HS256')
        refresh_token = secrets.token_urlsafe(32)
        user.refresh_token = refresh_token
        user.refresh_token_expire = datetime.now() + dt.timedelta(days=7)
        update_user_by_id(user)
        return make_succ_response({'token': token, 'refresh_token': refresh_token, 'user_id': user.user_id})
    except Exception as e:
        app.logger.error(f'手机号注册失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'注册失败: {str(e)}')


def _migrate_user_data(src_user_id, dst_user_id):
    try:
        rules = CheckinRule.query.filter(
            CheckinRule.solo_user_id == src_user_id,
            CheckinRule.status != 2  # 排除已删除的规则
        ).all()
        for r in rules:
            r.solo_user_id = dst_user_id
        records = CheckinRecord.query.filter(
            CheckinRecord.solo_user_id == src_user_id).all()
        for rec in records:
            rec.solo_user_id = dst_user_id
        rels = SupervisionRuleRelation.query.filter(
            SupervisionRuleRelation.solo_user_id == src_user_id).all()
        for rel in rels:
            rel.solo_user_id = dst_user_id
        rels2 = SupervisionRuleRelation.query.filter(
            SupervisionRuleRelation.supervisor_user_id == src_user_id).all()
        for rel in rels2:
            rel.supervisor_user_id = dst_user_id
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e


@app.route('/api/user/bind_phone', methods=['POST'])
@login_required
def bind_phone(decoded):
    try:
        params = request.get_json() or {}
        phone = params.get('phone')
        code = params.get('code')
        if not phone or not code:
            return make_err_response({}, '缺少phone或code参数')
        if not _verify_sms_code(phone, 'bind_phone', code):
            return make_err_response({}, '验证码无效或已过期')
        current_user = query_user_by_openid(decoded.get('openid'))
        if not current_user:
            return make_err_response({}, '用户不存在')
        phone_secret = os.getenv('PHONE_ENC_SECRET', 'default_secret')
        phone_hash = sha256(
            f"{phone_secret}:{phone}".encode('utf-8')).hexdigest()
        target = User.query.filter_by(phone_hash=phone_hash).first()
        if target and target.user_id != current_user.user_id:
            _migrate_user_data(target.user_id, current_user.user_id)
            target.status = 2
            db.session.commit()
        current_user.phone_hash = phone_hash
        current_user.phone_number = phone[:3] + '****' + \
            phone[-4:] if len(phone) >= 7 else phone
        update_user_by_id(current_user)
        _audit(current_user.user_id, 'bind_phone', {'phone': phone})
        return make_succ_response({'message': '绑定手机号成功'})
    except Exception as e:
        app.logger.error(f'绑定手机号失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'绑定手机号失败: {str(e)}')


@app.route('/api/user/bind_wechat', methods=['POST'])
@login_required
def bind_wechat(decoded):
    try:
        params = request.get_json() or {}
        wx_code = params.get('code')
        phone_code = params.get('phone_code')
        phone = params.get('phone')
        if not wx_code:
            return make_err_response({}, '缺少code参数')
        if phone and not _verify_sms_code(phone, 'bind_wechat', phone_code or ''):
            return make_err_response({}, '手机号验证码无效或已过期')
        from .wxchat_api import get_user_info_by_code
        wx_data = get_user_info_by_code(wx_code)
        if 'errcode' in wx_data:
            return make_err_response({}, f"微信API错误: {wx_data.get('errmsg', '未知错误')}")
        openid = wx_data.get('openid')
        if not openid:
            return make_err_response({}, '微信返回数据不完整')
        current_user = query_user_by_openid(decoded.get('openid'))
        if not current_user:
            return make_err_response({}, '用户不存在')
        existing_wechat = query_user_by_openid(openid)
        if existing_wechat and existing_wechat.user_id != current_user.user_id:
            _migrate_user_data(current_user.user_id, existing_wechat.user_id)
            current_user.status = 2
            db.session.commit()
            _audit(existing_wechat.user_id, 'bind_wechat_merge',
                   {'from_user_id': current_user.user_id})
            return make_succ_response({'message': '微信绑定并合并成功'})
        current_user.wechat_openid = openid
        update_user_by_id(current_user)
        _audit(current_user.user_id, 'bind_wechat', {'openid': openid})
        return make_succ_response({'message': '绑定微信成功'})
    except Exception as e:
        app.logger.error(f'绑定微信失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'绑定微信失败: {str(e)}')


@app.route('/api/community/verify', methods=['POST'])
def community_verify():
    """
    社区工作人员身份验证接口
    """
    app.logger.info('=== 开始执行社区工作人员身份验证接口 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    openid = decoded.get('openid')
    user = query_user_by_openid(openid)
    if not user:
        app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    try:
        # 获取请求参数
        params = request.get_json()
        name = params.get('name')
        work_id = params.get('workId')  # 注意：前端使用驼峰命名
        work_proof = params.get('workProof')  # 工作证明照片URL或base64

        if not name or not work_id or not work_proof:
            return make_err_response({}, '缺少必要参数：姓名、工号或工作证明')

        # 这里应该实现身份验证逻辑
        # 1. 保存验证信息到数据库
        # 2. 设置用户验证状态
        # 3. 模拟验证过程

        # 更新用户信息，设置验证状态
        user.name = name  # 添加姓名字段（如果模型中没有需要扩展）
        user.work_id = work_id  # 添加工号字段（如果模型中没有需要扩展）
        user.verification_status = 1  # 设置为待审核状态
        user.verification_materials = work_proof  # 保存验证材料
        user.updated_at = datetime.now()

        update_user_by_id(user)

        response_data = {
            'message': '身份验证申请已提交，请耐心等待审核',
            'verification_status': 'pending'
        }

        app.logger.info(f'用户 {user.user_id} 身份验证申请已提交')
        return make_succ_response(response_data)

    except Exception as e:
        app.logger.error(f'身份验证时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'身份验证失败: {str(e)}')


# 扩展User模型以支持身份验证相关字段
# 注意：由于无法直接修改已导入的模型，我们在数据库层面处理


def add_verification_fields():
    """
    为用户表添加身份验证相关字段
    """
    try:
        # 检查并添加必要的字段
        with db.engine.connect() as conn:
            # 检查是否已存在验证相关字段
            # 添加姓名字段
            try:
                conn.execute(
                    text("ALTER TABLE users ADD COLUMN name VARCHAR(100) COMMENT '真实姓名'"))
            except:
                pass  # 字段可能已存在

            # 添加工号字段
            try:
                conn.execute(
                    text("ALTER TABLE users ADD COLUMN work_id VARCHAR(50) COMMENT '工号或身份证号'"))
            except:
                pass  # 字段可能已存在

            # 添加验证状态字段
            try:
                conn.execute(text(
                    "ALTER TABLE users ADD COLUMN verification_status INTEGER DEFAULT 0 COMMENT '验证状态：0-未申请/1-待审核/2-已通过/3-已拒绝'"))
            except:
                pass  # 字段可能已存在

            # 添加验证材料字段
            try:
                conn.execute(text(
                    "ALTER TABLE users ADD COLUMN verification_materials TEXT COMMENT '验证材料URL'"))
            except:
                pass  # 字段可能已存在

            conn.commit()
    except Exception as e:
        app.logger.error(f'添加验证字段时发生错误: {str(e)}')

# 在应用启动后初始化验证字段
# with app.app_context():
#     init_verification_fields()


@app.route('/api/checkin/today', methods=['GET'])
@login_required
def get_today_checkin_items(decoded):
    """
    获取用户今日打卡事项列表
    """
    app.logger.info('=== 开始执行获取今日打卡事项接口 ===')

    openid = decoded.get('openid')
    user = query_user_by_openid(openid)
    if not user:
        app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    try:
        # 获取用户的打卡规则
        checkin_rules = query_checkin_rules_by_user_id(user.user_id)

        # 生成今天的打卡计划
        today = date.today()
        checkin_items = []
        for rule in checkin_rules:
            # 根据规则频率类型判断今天是否需要打卡
            should_checkin_today = True

            if rule.frequency_type == 1:  # 每周
                # 根据week_days位掩码判断今天是否需要打卡
                today_weekday = today.weekday()  # 0是周一，6是周日
                if not (rule.week_days & (1 << today_weekday)):
                    should_checkin_today = False
            elif rule.frequency_type == 2:  # 工作日
                if today.weekday() >= 5:  # 周六日
                    should_checkin_today = False

            if should_checkin_today:
                # 查询今天该规则的打卡记录
                today_records = query_checkin_records_by_rule_id_and_date(
                    rule.rule_id, today)

                # 计算计划打卡时间
                if rule.time_slot_type == 4 and rule.custom_time:  # 自定义时间
                    planned_time = datetime.combine(today, rule.custom_time)
                elif rule.time_slot_type == 1:  # 上午
                    planned_time = datetime.combine(
                        today, time(9, 0))  # 默认上午9点
                elif rule.time_slot_type == 2:  # 下午
                    planned_time = datetime.combine(
                        today, time(14, 0))  # 默认下午2点
                else:  # 晚上，默认晚上8点
                    planned_time = datetime.combine(today, time(20, 0))

                # 确定打卡状态
                checkin_status = 'unchecked'
                checkin_time = None
                record_id = None

                for record in today_records:
                    if record.status == 1:  # 已打卡
                        checkin_status = 'checked'
                        checkin_time = record.checkin_time.strftime(
                            '%H:%M:%S') if record.checkin_time else None
                        record_id = record.record_id
                        break
                    elif record.status == 2:  # 已撤销
                        checkin_status = 'unchecked'
                        checkin_time = None
                        record_id = record.record_id
                        break

                checkin_items.append({
                    'rule_id': rule.rule_id,
                    'record_id': record_id,
                    'rule_name': rule.rule_name,
                    'icon_url': rule.icon_url,
                    'planned_time': planned_time.strftime('%H:%M:%S'),
                    'status': checkin_status,  # unchecked, checked
                    'checkin_time': checkin_time
                })

        response_data = {
            'date': today.strftime('%Y-%m-%d'),
            'checkin_items': checkin_items
        }

        app.logger.info(
            f'成功获取今日打卡事项，用户ID: {user.user_id}, 事项数量: {len(checkin_items)}')
        return make_succ_response(response_data)

    except Exception as e:
        app.logger.error(f'获取今日打卡事项时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取今日打卡事项失败: {str(e)}')


@app.route('/api/checkin', methods=['POST'])
@login_required
def perform_checkin(decoded):
    """
    执行打卡操作
    """
    app.logger.info('=== 开始执行打卡接口 ===')

    openid = decoded.get('openid')
    user = query_user_by_openid(openid)
    if not user:
        app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    try:
        # 获取请求参数
        params = request.get_json()
        rule_id = params.get('rule_id')

        if not rule_id:
            return make_err_response({}, '缺少rule_id参数')

        # 验证打卡规则是否存在且属于当前用户
        rule = query_checkin_rule_by_id(rule_id)
        if not rule or rule.solo_user_id != user.user_id:
            return make_err_response({}, '打卡规则不存在或无权限')

        # 检查今天是否已有打卡记录（防止重复打卡）
        today = date.today()
        existing_records = query_checkin_records_by_rule_id_and_date(
            rule_id, today)

        # 查找当天已有的打卡记录（状态为已打卡）
        existing_checkin = None
        for record in existing_records:
            if record.status == 1:  # 已打卡
                # 不允许重复打卡
                return make_err_response({}, '今日该事项已打卡，请勿重复打卡')
            elif record.status == 0:  # 未打卡状态的记录，可以更新为已打卡
                existing_checkin = record
                break
            elif record.status == 2:  # 已撤销的记录，可以重新打卡
                # 创建新的打卡记录
                existing_checkin = None
                break

        # 记录打卡时间
        checkin_time = datetime.now()

        if existing_checkin:
            # 更新已有记录的打卡时间和状态
            existing_checkin.checkin_time = checkin_time
            existing_checkin.status = 1  # 已打卡
            update_checkin_record_by_id(existing_checkin)
            record_id = existing_checkin.record_id
        else:
            # 计算计划打卡时间
            if rule.time_slot_type == 4 and rule.custom_time:  # 自定义时间
                planned_time = datetime.combine(today, rule.custom_time)
            elif rule.time_slot_type == 1:  # 上午
                planned_time = datetime.combine(today, time(9, 0))  # 默认上午9点
            elif rule.time_slot_type == 2:  # 下午
                planned_time = datetime.combine(today, time(14, 0))  # 默认下午2点
            else:  # 晚上，默认晚上8点
                planned_time = datetime.combine(today, time(20, 0))

            # 创建新的打卡记录
            new_record = CheckinRecord(
                rule_id=rule_id,
                solo_user_id=user.user_id,
                checkin_time=checkin_time,
                status=1,  # 已打卡
                planned_time=planned_time
            )
            insert_checkin_record(new_record)
            record_id = new_record.record_id

        response_data = {
            'rule_id': rule_id,
            'record_id': record_id,
            'checkin_time': checkin_time.strftime('%Y-%m-%d %H:%M:%S'),
            'message': '打卡成功'
        }

        app.logger.info(f'用户 {user.user_id} 打卡成功，规则ID: {rule_id}')
        return make_succ_response(response_data)

    except Exception as e:
        app.logger.error(f'打卡时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'打卡失败: {str(e)}')


@app.route('/api/checkin/miss', methods=['POST'])
@login_required
def mark_missed(decoded):
    """
    标记当天规则为missed（超过宽限期）
    """
    app.logger.info('=== 开始执行标记miss接口 ===')

    openid = decoded.get('openid')
    user = query_user_by_openid(openid)
    if not user:
        app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    try:
        params = request.get_json() or {}
        rule_id = params.get('rule_id')
        if not rule_id:
            return make_err_response({}, '缺少rule_id参数')
        rule = query_checkin_rule_by_id(rule_id)
        if not rule or rule.solo_user_id != user.user_id:
            return make_err_response({}, '打卡规则不存在或无权限')

        today = date.today()
        records = query_checkin_records_by_rule_id_and_date(rule_id, today)
        for r in records:
            if r.status == 1:
                return make_err_response({}, '今日该事项已打卡，无需标记miss')

        if rule.time_slot_type == 4 and rule.custom_time:
            planned_time = datetime.combine(today, rule.custom_time)
        elif rule.time_slot_type == 1:
            planned_time = datetime.combine(today, time(9, 0))
        elif rule.time_slot_type == 2:
            planned_time = datetime.combine(today, time(14, 0))
        else:
            planned_time = datetime.combine(today, time(20, 0))

        new_record = CheckinRecord(
            rule_id=rule_id,
            solo_user_id=user.user_id,
            checkin_time=None,
            status=0,
            planned_time=planned_time
        )
        insert_checkin_record(new_record)

        return make_succ_response({'record_id': new_record.record_id, 'message': '已标记为miss'})
    except Exception as e:
        app.logger.error(f'标记miss时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'标记miss失败: {str(e)}')


@app.route('/api/checkin/cancel', methods=['POST'])
@login_required
def cancel_checkin(decoded):
    """
    撤销打卡操作（仅限30分钟内）
    """
    app.logger.info('=== 开始执行撤销打卡接口 ===')

    openid = decoded.get('openid')
    user = query_user_by_openid(openid)
    if not user:
        app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    try:
        # 获取请求参数
        params = request.get_json()
        record_id = params.get('record_id')

        if not record_id:
            return make_err_response({}, '缺少record_id参数')

        # 验证打卡记录是否存在且属于当前用户
        record = query_checkin_record_by_id(record_id)
        if not record or record.solo_user_id != user.user_id:
            return make_err_response({}, '打卡记录不存在或无权限')

        # 检查打卡时间是否在30分钟内（防止撤销过期打卡）
        if record.checkin_time:
            time_diff = datetime.now() - record.checkin_time
            if time_diff.total_seconds() > 30 * 60:  # 30分钟
                return make_err_response({}, '只能撤销30分钟内的打卡记录')

        # 更新记录状态为已撤销
        record.status = 2  # 已撤销
        record.checkin_time = None  # 清除打卡时间
        update_checkin_record_by_id(record)

        response_data = {
            'record_id': record_id,
            'message': '撤销打卡成功'
        }

        app.logger.info(f'用户 {user.user_id} 撤销打卡成功，记录ID: {record_id}')
        return make_succ_response(response_data)

    except Exception as e:
        app.logger.error(f'撤销打卡时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'撤销打卡失败: {str(e)}')


@app.route('/api/checkin/history', methods=['GET'])
@login_required
def get_checkin_history(decoded):
    """
    获取打卡历史记录
    """
    app.logger.info('=== 开始执行获取打卡历史接口 ===')

    openid = decoded.get('openid')
    user = query_user_by_openid(openid)
    if not user:
        app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    try:
        # 获取查询参数
        params = request.args
        start_date_str = params.get(
            'start_date', (date.today() - timedelta(days=7)).strftime('%Y-%m-%d'))
        end_date_str = params.get(
            'end_date', date.today().strftime('%Y-%m-%d'))

        # 解析日期
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

        # 获取打卡记录
        records = query_checkin_records_by_user_and_date_range(
            user.user_id, start_date, end_date)

        # 转换为响应格式
        history_data = []
        for record in records:
            history_data.append({
                'record_id': record.record_id,
                'rule_id': record.rule_id,
                'rule_name': record.rule.rule_name,
                'icon_url': record.rule.icon_url,
                'planned_time': record.planned_time.strftime('%Y-%m-%d %H:%M:%S'),
                'checkin_time': record.checkin_time.strftime('%Y-%m-%d %H:%M:%S') if record.checkin_time else None,
                'status': record.status_name,  # 使用模型中的状态名称
                'created_at': record.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })

        response_data = {
            'start_date': start_date_str,
            'end_date': end_date_str,
            'history': history_data
        }

        app.logger.info(
            f'成功获取打卡历史，用户ID: {user.user_id}, 记录数量: {len(history_data)}')
        return make_succ_response(response_data)

    except Exception as e:
        app.logger.error(f'获取打卡历史时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取打卡历史失败: {str(e)}')


@app.route('/api/checkin/rules', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def manage_checkin_rules(decoded):
    """
    打卡规则管理接口
    GET: 获取打卡规则列表
    POST: 创建打卡规则
    PUT: 更新打卡规则
    DELETE: 删除打卡规则
    """
    app.logger.info(f'=== 开始执行打卡规则管理接口: {request.method} ===')

    openid = decoded.get('openid')
    user = query_user_by_openid(openid)
    if not user:
        app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    try:
        def parse_time(v):
            if not v:
                return None
            try:
                return datetime.strptime(v, '%H:%M:%S').time()
            except Exception:
                return datetime.strptime(v, '%H:%M').time()

        def format_time(t):
            return t.strftime('%H:%M') if t else None

        def parse_date(v):
            if not v:
                return None
            return datetime.strptime(v, '%Y-%m-%d').date()
        if request.method == 'GET':
            # 获取用户的所有打卡规则
            rules = query_checkin_rules_by_user_id(user.user_id)

            rules_data = []
            for rule in rules:
                rules_data.append({
                    'rule_id': rule.rule_id,
                    'rule_name': rule.rule_name,
                    'icon_url': rule.icon_url,
                    'frequency_type': rule.frequency_type,
                    'time_slot_type': rule.time_slot_type,
                    'custom_time': format_time(rule.custom_time),
                    'week_days': rule.week_days,
                    'custom_start_date': rule.custom_start_date.strftime('%Y-%m-%d') if rule.custom_start_date else None,
                    'custom_end_date': rule.custom_end_date.strftime('%Y-%m-%d') if rule.custom_end_date else None,
                    'status': rule.status,
                    'created_at': rule.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_at': rule.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                })

            response_data = {
                'rules': rules_data
            }

            app.logger.info(
                f'成功获取打卡规则列表，用户ID: {user.user_id}, 规则数量: {len(rules_data)}')
            return make_succ_response(response_data)

        elif request.method == 'POST':
            params = request.get_json()

            rule_name = params.get('rule_name')
            if not rule_name:
                app.logger.error('❌ Layer 4验证失败: 缺少rule_name参数')
                return make_err_response({}, '缺少rule_name参数')

            # 创建新的打卡规则
            freq = params.get('frequency_type', 0)
            start_date = parse_date(params.get('custom_start_date'))
            end_date = parse_date(params.get('custom_end_date'))
            if int(freq) == 3:
                if not start_date or not end_date:
                    return make_err_response({}, '自定义频率必须提供起止日期')
                if end_date < start_date:
                    return make_err_response({}, '结束日期不能早于开始日期')

            new_rule = CheckinRule(
                solo_user_id=user.user_id,
                rule_name=rule_name,
                icon_url=params.get('icon_url', ''),
                frequency_type=freq,  # 默认每天
                time_slot_type=params.get('time_slot_type', 4),  # 默认自定义时间
                custom_time=parse_time(params.get('custom_time')),
                week_days=params.get('week_days', 127),  # 默认周一到周日
                custom_start_date=start_date,
                custom_end_date=end_date,
                status=params.get('status', 1)  # 默认启用
            )

            try:
                insert_checkin_rule(new_rule)
            except Exception as db_error:
                import traceback
                app.logger.error(f'数据库错误堆栈: {traceback.format_exc()}')
                return make_err_response({}, f'数据库保存失败: {str(db_error)}')

            response_data = {
                'rule_id': new_rule.rule_id,
                'message': '创建打卡规则成功'
            }

            app.logger.info(
                f'成功创建打卡规则，用户ID: {user.user_id}, 规则ID: {new_rule.rule_id}')
            return make_succ_response(response_data)

        elif request.method == 'PUT':
            # 更新打卡规则
            params = request.get_json()

            rule_id = params.get('rule_id')
            if not rule_id:
                return make_err_response({}, '缺少rule_id参数')

            # 验证规则是否存在且属于当前用户
            rule = query_checkin_rule_by_id(rule_id)
            if not rule or rule.solo_user_id != user.user_id:
                return make_err_response({}, '打卡规则不存在或无权限')

            # 更新规则信息
            if 'rule_name' in params:
                rule.rule_name = params['rule_name']
            if 'icon_url' in params:
                rule.icon_url = params['icon_url']
            if 'frequency_type' in params:
                rule.frequency_type = params['frequency_type']
            if 'time_slot_type' in params:
                rule.time_slot_type = params['time_slot_type']
            if 'custom_time' in params:
                rule.custom_time = parse_time(
                    params['custom_time']) if params['custom_time'] else None
            if 'week_days' in params:
                rule.week_days = params['week_days']
            if 'status' in params:
                rule.status = params['status']
            if 'custom_start_date' in params:
                rule.custom_start_date = parse_date(
                    params['custom_start_date']) if params['custom_start_date'] else None
            if 'custom_end_date' in params:
                rule.custom_end_date = parse_date(
                    params['custom_end_date']) if params['custom_end_date'] else None

            # 校验自定义频率的日期范围
            final_freq = params.get('frequency_type', rule.frequency_type)
            if int(final_freq) == 3:
                if not rule.custom_start_date or not rule.custom_end_date:
                    return make_err_response({}, '自定义频率必须提供起止日期')
                if rule.custom_end_date < rule.custom_start_date:
                    return make_err_response({}, '结束日期不能早于开始日期')

            update_checkin_rule_by_id(rule)

            response_data = {
                'rule_id': rule.rule_id,
                'message': '更新打卡规则成功'
            }

            app.logger.info(
                f'成功更新打卡规则，用户ID: {user.user_id}, 规则ID: {rule.rule_id}')
            return make_succ_response(response_data)

        elif request.method == 'DELETE':
            # 删除打卡规则
            params = request.get_json()

            rule_id = params.get('rule_id')
            if not rule_id:
                return make_err_response({}, '缺少rule_id参数')

            # 验证规则是否存在且属于当前用户
            rule = query_checkin_rule_by_id(rule_id)
            if not rule or rule.solo_user_id != user.user_id:
                return make_err_response({}, '打卡规则不存在或无权限')

            try:
                delete_checkin_rule_by_id(rule_id)

                response_data = {
                    'rule_id': rule_id,
                    'message': '删除打卡规则成功'
                }

                app.logger.info(
                    f'成功删除打卡规则，用户ID: {user.user_id}, 规则ID: {rule_id}')
                return make_succ_response(response_data)
            except ValueError as e:
                # 处理规则不存在的异常
                app.logger.warning(f'删除打卡规则失败: {str(e)}, 用户ID: {user.user_id}')
                return make_err_response({}, str(e))
            except Exception as e:
                app.logger.error(
                    f'删除打卡规则时发生错误: {str(e)}, 用户ID: {user.user_id}')
                return make_err_response({}, f'删除打卡规则失败: {str(e)}')

    except Exception as e:
        app.logger.error(f'打卡规则管理时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'打卡规则管理失败: {str(e)}')


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
        user = query_user_by_refresh_token(refresh_token)
        if not user or not user.refresh_token or user.refresh_token != refresh_token:
            app.logger.warning(f'无效的refresh_token: {refresh_token[:20]}...')
            return make_err_response({}, '无效的refresh_token')

        # 检查refresh token是否过期
        from datetime import datetime
        if user.refresh_token_expire and user.refresh_token_expire < datetime.now():
            app.logger.warning(f'refresh_token已过期，用户ID: {user.user_id}')
            # 清除过期的refresh token
            user.refresh_token = None
            user.refresh_token_expire = None
            update_user_by_id(user)
            return make_err_response({}, 'refresh_token已过期')

        app.logger.info(f'找到用户，正在为用户ID: {user.user_id} 生成新token')

        # 生成新的JWT token（access token）
        import datetime as dt
        token_payload = {
            'openid': user.wechat_openid,
            'user_id': user.user_id,
            'exp': dt.datetime.utcnow() + dt.timedelta(hours=2)  # 设置2小时过期时间
        }
        try:
            token_secret = get_token_secret()
        except ValueError as e:
            app.logger.error(f'获取TOKEN_SECRET失败: {str(e)}')
            return make_err_response({}, '服务器配置错误')
        new_token = jwt.encode(token_payload, token_secret, algorithm='HS256')

        # 生成新的refresh token（可选：也可以继续使用现有的refresh token）
        import secrets
        new_refresh_token = secrets.token_urlsafe(32)
        # 设置新的refresh token过期时间（7天）
        new_refresh_token_expire = datetime.now() + dt.timedelta(days=7)

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


def query_user_by_refresh_token(refresh_token):
    """
    根据refresh token查询用户
    """
    try:
        from .dao import session
        user = session.query(User).filter(
            User.refresh_token == refresh_token).first()
        return user
    except Exception as e:
        app.logger.error(f'查询用户失败: {str(e)}')
        return None


@app.route('/api/logout', methods=['POST'])
@login_required
def logout(decoded):
    """
    用户登出接口，清除refresh token
    """
    app.logger.info('=== 开始执行登出接口 ===')

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


@app.route('/api/rules/supervision/invite', methods=['POST'])
@login_required
def invite_supervisor(decoded):
    """
    邀请监督者接口 - 邀请特定用户监督特定规则
    """
    app.logger.info('=== 开始执行邀请监督者接口 ===')

    openid = decoded.get('openid')
    user = query_user_by_openid(openid)
    if not user:
        app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    try:
        # 获取请求参数
        params = request.get_json()
        invite_type = params.get(
            'invite_type', 'wechat')  # 邀请类型：wechat, phone等
        rule_ids = params.get('rule_ids', [])  # 要监督的规则ID列表，空表示监督所有规则
        target_openid = params.get('target_openid')  # 被邀请用户的openid

        if not target_openid:
            return make_err_response({}, '缺少target_openid参数')

        # 查询被邀请用户
        target_user = query_user_by_openid(target_openid)
        if not target_user:
            return make_err_response({}, '被邀请用户不存在')

        # 检查规则是否都属于当前用户
        if rule_ids:
            for rule_id in rule_ids:
                rule = query_checkin_rule_by_id(rule_id)
                if not rule or rule.solo_user_id != user.user_id:
                    return make_err_response({}, f'规则ID {rule_id} 不存在或不属于当前用户')

        # 创建监督关系 - 为每个规则创建一条记录，如果rule_ids为空则创建一条规则ID为null的记录
        if not rule_ids:  # 监督所有规则
            # 检查是否已存在监督关系
            existing_relation = SupervisionRuleRelation.query.filter_by(
                solo_user_id=user.user_id,
                supervisor_user_id=target_user.user_id,
                rule_id=None,
                status=1  # 待同意
            ).first()

            if not existing_relation:
                new_relation = SupervisionRuleRelation(
                    solo_user_id=user.user_id,
                    supervisor_user_id=target_user.user_id,
                    rule_id=None,  # 表示监督所有规则
                    status=1  # 待同意
                )
                db.session.add(new_relation)
                db.session.commit()
        else:  # 监督特定规则
            for rule_id in rule_ids:
                # 检查是否已存在监督关系
                existing_relation = SupervisionRuleRelation.query.filter_by(
                    solo_user_id=user.user_id,
                    supervisor_user_id=target_user.user_id,
                    rule_id=rule_id,
                    status=1  # 待同意
                ).first()

                if not existing_relation:
                    new_relation = SupervisionRuleRelation(
                        solo_user_id=user.user_id,
                        supervisor_user_id=target_user.user_id,
                        rule_id=rule_id,
                        status=1  # 待同意
                    )
                    db.session.add(new_relation)

        db.session.commit()

        response_data = {
            'message': '邀请发送成功'
        }

        app.logger.info(f'用户 {user.user_id} 邀请用户 {target_user.user_id} 监督规则成功')
        return make_succ_response(response_data)
    except Exception as e:
        app.logger.error(f'邀请监督者时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'邀请监督者失败: {str(e)}')


@app.route('/api/rules/supervision/invite_link', methods=['POST'])
@login_required
def invite_supervisor_link(decoded):
    """
    生成监督邀请链接（无需目标openid）
    """
    app.logger.info('=== 开始执行生成监督邀请链接接口 ===')
    openid = decoded.get('openid')
    user = query_user_by_openid(openid)
    if not user:
        return make_err_response({}, '用户不存在')

    try:
        params = request.get_json() or {}
        rule_ids = params.get('rule_ids', [])
        expire_hours = int(params.get('expire_hours', 72))
        token = secrets.token_urlsafe(16)
        from datetime import timedelta as td
        expires_at = datetime.now() + td(hours=expire_hours)

        created_relations = []
        if rule_ids:
            for rid in rule_ids:
                rel = SupervisionRuleRelation(
                    solo_user_id=user.user_id,
                    supervisor_user_id=None,
                    rule_id=rid,
                    status=1,
                    invite_token=token,
                    invite_expires_at=expires_at
                )
                db.session.add(rel)
                created_relations.append(rel)
        else:
            rel = SupervisionRuleRelation(
                solo_user_id=user.user_id,
                supervisor_user_id=None,
                rule_id=None,
                status=1,
                invite_token=token,
                invite_expires_at=expires_at
            )
            db.session.add(rel)
            created_relations.append(rel)

        db.session.commit()

        response_data = {
            'invite_token': token,
            'mini_path': f"/pages/supervisor-invite/supervisor-invite?token={token}",
            'expire_at': expires_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        return make_succ_response(response_data)
    except Exception as e:
        app.logger.error(f'生成监督邀请链接失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'生成监督邀请链接失败: {str(e)}')


@app.route('/api/share/checkin/create', methods=['POST'])
@login_required
def create_share_checkin_link(decoded):
    """
    创建可分享的打卡邀请链接（opaque token，避免暴露敏感参数）
    请求体：{ rule_id, expire_hours? 默认 168(7天) }
    返回：{ token, url, mini_path, expire_at }
    """
    try:
        openid = decoded.get('openid')
        user = query_user_by_openid(openid)
        if not user:
            return make_err_response({}, '用户不存在')

        params = request.get_json() or {}
        rule_id = params.get('rule_id')
        expire_hours = int(params.get('expire_hours', 168))
        if not rule_id:
            return make_err_response({}, '缺少rule_id参数')

        rule = query_checkin_rule_by_id(rule_id)
        if not rule or rule.solo_user_id != user.user_id:
            return make_err_response({}, '打卡规则不存在或无权限')

        import secrets
        token = secrets.token_urlsafe(16)
        from datetime import timedelta as td
        expires_at = datetime.now() + td(hours=expire_hours)

        link = ShareLink(
            token=token,
            solo_user_id=user.user_id,
            rule_id=rule.rule_id,
            expires_at=expires_at
        )
        db.session.add(link)
        db.session.commit()

        # 构造URL（PC/移动端），以及小程序内路径
        base = request.host_url.rstrip('/')
        url = f"{base}/share/check-in?token={token}"
        mini_path = f"/pages/supervisor-detail/supervisor-detail?token={token}"

        return make_succ_response({
            'token': token,
            'url': url,
            'mini_path': mini_path,
            'expire_at': expires_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        app.logger.error(f'创建分享链接失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'创建分享链接失败: {str(e)}')


@app.route('/api/share/checkin/resolve', methods=['GET'])
@login_required
def resolve_share_checkin_link(decoded):
    """
    解析分享链接并建立监督关系（已注册用户点击链接后）
    参数：token
    返回：完整规则信息
    """
    try:
        token = request.args.get('token')
        if not token:
            return make_err_response({}, '缺少token参数')

        link = ShareLink.query.filter_by(token=token).first()
        if not link:
            return make_err_response({}, '链接无效或已失效')
        if link.expires_at and link.expires_at < datetime.now():
            return make_err_response({}, '链接已过期')

        # 访问日志记录
        try:
            lg = ShareLinkAccessLog(
                token=token,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                supervisor_user_id=query_user_by_openid(
                    decoded.get('openid')).user_id
            )
            db.session.add(lg)
            db.session.commit()
        except Exception:
            pass

        # 建立监督关系，直接设为已同意
        relation = SupervisionRuleRelation.query.filter_by(
            solo_user_id=link.solo_user_id,
            supervisor_user_id=query_user_by_openid(
                decoded.get('openid')).user_id,
            rule_id=link.rule_id
        ).first()
        if not relation:
            relation = SupervisionRuleRelation(
                solo_user_id=link.solo_user_id,
                supervisor_user_id=query_user_by_openid(
                    decoded.get('openid')).user_id,
                rule_id=link.rule_id,
                status=2
            )
            db.session.add(relation)
        else:
            relation.status = 2
            relation.updated_at = datetime.now()
        db.session.commit()

        rule = query_checkin_rule_by_id(link.rule_id)
        rule_data = {
            'rule_id': rule.rule_id,
            'rule_name': rule.rule_name,
            'icon_url': rule.icon_url,
            'frequency_type': rule.frequency_type,
            'time_slot_type': rule.time_slot_type,
            'custom_time': rule.custom_time.strftime('%H:%M') if rule.custom_time else None,
            'week_days': rule.week_days,
            'custom_start_date': rule.custom_start_date.strftime('%Y-%m-%d') if rule.custom_start_date else None,
            'custom_end_date': rule.custom_end_date.strftime('%Y-%m-%d') if rule.custom_end_date else None,
            'status': rule.status
        }
        return make_succ_response({'rule': rule_data, 'solo_user_id': link.solo_user_id})
    except Exception as e:
        app.logger.error(f'解析分享链接失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'解析分享链接失败: {str(e)}')


@app.route('/share/check-in', methods=['GET'])
def share_checkin_page():
    """
    分享链接的Web入口：
    - 记录访问日志
    - 微信UA下提示小程序路径
    - 如果提供了Authorization则自动解析并返回JSON
    """
    try:
        token = request.args.get('token')
        if not token:
            return make_err_response({}, '缺少token参数')
        link = ShareLink.query.filter_by(token=token).first()
        if not link:
            return make_err_response({}, '链接无效或已失效')
        if link.expires_at and link.expires_at < datetime.now():
            return make_err_response({}, '链接已过期')

        # 访问日志
        try:
            lg = ShareLinkAccessLog(
                token=token,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(lg)
            db.session.commit()
        except Exception:
            pass

        ua = request.headers.get('User-Agent', '')
        is_wechat = 'MicroMessenger' in ua

        # 如果携带了Authorization，可以直接走解析逻辑
        auth_header = request.headers.get('Authorization', '')
        if auth_header:
            decoded, err = verify_token()
            if not err:
                # 复用解析逻辑
                with app.app_context():
                    # 建立监督关系
                    supervisor_user = query_user_by_openid(
                        decoded.get('openid'))
                    relation = SupervisionRuleRelation.query.filter_by(
                        solo_user_id=link.solo_user_id,
                        supervisor_user_id=supervisor_user.user_id,
                        rule_id=link.rule_id
                    ).first()
                    if not relation:
                        relation = SupervisionRuleRelation(
                            solo_user_id=link.solo_user_id,
                            supervisor_user_id=supervisor_user.user_id,
                            rule_id=link.rule_id,
                            status=2
                        )
                        db.session.add(relation)
                    else:
                        relation.status = 2
                        relation.updated_at = datetime.now()
                    db.session.commit()
                rule = query_checkin_rule_by_id(link.rule_id)
                return make_succ_response({
                    'message': '解析成功',
                    'rule': {
                        'rule_id': rule.rule_id,
                        'rule_name': rule.rule_name,
                        'icon_url': rule.icon_url
                    },
                    'solo_user_id': link.solo_user_id
                })

        # 微信环境返回提示页面
        if is_wechat:
            mini_path = f"/pages/supervisor-detail/supervisor-detail?token={token}"
            html = f"""
            <html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>
            <title>打开打卡规则</title></head>
            <body>
            <p>请在微信小程序中打开以下路径：</p>
            <pre>{mini_path}</pre>
            </body></html>
            """
            return html

        # 非微信环境返回基础提示
        base = request.host_url.rstrip('/')
        front_url = f"{base}/#/supervisor-detail?token={token}"
        html = f"""
        <html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>
        <title>打开打卡规则</title></head>
        <body>
        <p>请在前端页面打开规则详情：</p>
        <a href='{front_url}'>{front_url}</a>
        </body></html>
        """
        return html
    except Exception as e:
        app.logger.error(f'分享页面处理失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'分享页面处理失败: {str(e)}')


@app.route('/api/rules/supervision/invite/resolve', methods=['GET'])
@login_required
def resolve_invite_link(decoded):
    """
    解析邀请链接，将当前登录用户绑定为supervisor
    """
    app.logger.info('=== 开始执行解析邀请链接接口 ===')
    openid = decoded.get('openid')
    user = query_user_by_openid(openid)
    if not user:
        return make_err_response({}, '用户不存在')

    try:
        token = request.args.get('token')
        if not token:
            return make_err_response({}, '缺少token参数')

        relation = SupervisionRuleRelation.query.filter_by(
            invite_token=token).first()
        if not relation:
            return make_err_response({}, '邀请链接无效或已失效')

        if relation.invite_expires_at and relation.invite_expires_at < datetime.now():
            return make_err_response({}, '邀请链接已过期')

        if relation.supervisor_user_id and relation.supervisor_user_id != user.user_id:
            return make_err_response({}, '邀请已被其他用户处理')

        relation.supervisor_user_id = user.user_id
        relation.updated_at = datetime.now()
        db.session.commit()

        response_data = {
            'relation_id': relation.relation_id,
            'status': relation.status_name,
            'solo_user_id': relation.solo_user_id,
            'rule_id': relation.rule_id
        }
        return make_succ_response(response_data)
    except Exception as e:
        app.logger.error(f'解析邀请链接失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'解析邀请链接失败: {str(e)}')


@app.route('/api/rules/supervision/invitations', methods=['GET'])
@login_required
def get_supervision_invitations(decoded):
    """
    获取监督邀请列表接口 - 获取当前用户收到的监督邀请
    """
    app.logger.info('=== 开始执行获取监督邀请列表接口 ===')

    openid = decoded.get('openid')
    user = query_user_by_openid(openid)
    if not user:
        app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    try:
        inv_type = request.args.get('type', 'received')
        if inv_type == 'sent':
            invitations = SupervisionRuleRelation.query.filter_by(
                solo_user_id=user.user_id,
                status=1
            ).all()
        else:
            invitations = SupervisionRuleRelation.query.filter_by(
                supervisor_user_id=user.user_id,
                status=1
            ).all()

        invitations_data = []
        for inv in invitations:
            solo_user = query_user_by_id(inv.solo_user_id)
            rule_info = None
            if inv.rule_id:
                rule = query_checkin_rule_by_id(inv.rule_id)
                if rule:
                    rule_info = {
                        'rule_id': rule.rule_id,
                        'rule_name': rule.rule_name
                    }

            invitations_data.append({
                'relation_id': inv.relation_id,
                'solo_user': {
                    'user_id': solo_user.user_id,
                    'nickname': solo_user.nickname,
                    'avatar_url': solo_user.avatar_url
                },
                'rule': rule_info,
                'status': inv.status_name,
                'created_at': inv.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })

        response_data = {
            'type': inv_type,
            'invitations': invitations_data
        }

        app.logger.info(
            f'成功获取监督邀请列表，用户ID: {user.user_id}, 邀请数量: {len(invitations_data)}')
        return make_succ_response(response_data)

    except Exception as e:
        app.logger.error(f'获取监督邀请列表时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取监督邀请列表失败: {str(e)}')


@app.route('/api/rules/supervision/accept', methods=['POST'])
@login_required
def accept_supervision_invitation(decoded):
    """
    接受监督邀请接口
    """
    app.logger.info('=== 开始执行接受监督邀请接口 ===')

    openid = decoded.get('openid')
    user = query_user_by_openid(openid)
    if not user:
        app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    try:
        # 获取请求参数
        params = request.get_json()
        relation_id = params.get('relation_id')

        if not relation_id:
            return make_err_response({}, '缺少relation_id参数')

        # 查找邀请关系
        relation = SupervisionRuleRelation.query.get(relation_id)
        if not relation or relation.supervisor_user_id != user.user_id:
            return make_err_response({}, '邀请关系不存在或无权限')

        # 检查是否已经是已同意状态
        if relation.status == 2:  # 已同意
            return make_err_response({}, '邀请已接受')

        # 更新状态为已同意
        relation.status = 2  # 已同意
        relation.updated_at = datetime.now()
        db.session.commit()

        response_data = {
            'message': '接受邀请成功'
        }

        app.logger.info(f'用户 {user.user_id} 接受监督邀请成功，关系ID: {relation_id}')
        return make_succ_response(response_data)

    except Exception as e:
        app.logger.error(f'接受监督邀请时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'接受监督邀请失败: {str(e)}')


@app.route('/api/rules/supervision/reject', methods=['POST'])
@login_required
def reject_supervision_invitation(decoded):
    """
    拒绝监督邀请接口
    """
    app.logger.info('=== 开始执行拒绝监督邀请接口 ===')

    openid = decoded.get('openid')
    user = query_user_by_openid(openid)
    if not user:
        app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    try:
        # 获取请求参数
        params = request.get_json()
        relation_id = params.get('relation_id')

        if not relation_id:
            return make_err_response({}, '缺少relation_id参数')

        # 查找邀请关系
        relation = SupervisionRuleRelation.query.get(relation_id)
        if not relation or relation.supervisor_user_id != user.user_id:
            return make_err_response({}, '邀请关系不存在或无权限')

        # 更新状态为已拒绝
        relation.status = 3  # 已拒绝
        relation.updated_at = datetime.now()
        db.session.commit()

        response_data = {
            'message': '拒绝邀请成功'
        }

        app.logger.info(f'用户 {user.user_id} 拒绝监督邀请成功，关系ID: {relation_id}')
        return make_succ_response(response_data)

    except Exception as e:
        app.logger.error(f'拒绝监督邀请时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'拒绝监督邀请失败: {str(e)}')


@app.route('/api/rules/supervision/my_supervised', methods=['GET'])
@login_required
def get_my_supervised_users(decoded):
    """
    获取我监督的用户列表接口
    """
    app.logger.info('=== 开始执行获取我监督的用户列表接口 ===')

    openid = decoded.get('openid')
    user = query_user_by_openid(openid)
    if not user:
        app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    try:
        # 获取当前用户监督的用户列表
        supervised_users = user.get_supervised_users()

        supervised_data = []
        for solo_user in supervised_users:
            # 获取被监督用户的规则列表
            rules = user.get_supervised_rules(solo_user.user_id)
            rule_list = [{
                'rule_id': rule.rule_id,
                'rule_name': rule.rule_name,
                'icon_url': rule.icon_url
            } for rule in rules]

            # 获取被监督用户今天的打卡状态
            today = date.today()
            checkin_items = []
            for rule in rules:
                # 查询今天该规则的打卡记录
                today_records = query_checkin_records_by_rule_id_and_date(
                    rule.rule_id, today)

                # 确定打卡状态
                checkin_status = 'unchecked'
                checkin_time = None

                for record in today_records:
                    if record.status == 1:  # 已打卡
                        checkin_status = 'checked'
                        checkin_time = record.checkin_time.strftime(
                            '%H:%M:%S') if record.checkin_time else None
                        break
                    elif record.status == 2:  # 已撤销
                        checkin_status = 'unchecked'
                        checkin_time = None
                        break

                checkin_items.append({
                    'rule_id': rule.rule_id,
                    'rule_name': rule.rule_name,
                    'status': checkin_status,
                    'checkin_time': checkin_time
                })

            supervised_data.append({
                'user_id': solo_user.user_id,
                'nickname': solo_user.nickname,
                'avatar_url': solo_user.avatar_url,
                'rules': rule_list,
                'today_checkin_status': checkin_items
            })

        response_data = {
            'supervised_users': supervised_data
        }

        app.logger.info(
            f'成功获取监督的用户列表，用户ID: {user.user_id}, 监督数量: {len(supervised_data)}')
        return make_succ_response(response_data)

    except Exception as e:
        app.logger.error(f'获取监督的用户列表时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取监督的用户列表失败: {str(e)}')


@app.route('/api/rules/supervision/my_guardians', methods=['GET'])
@login_required
def get_my_guardians(decoded):
    app.logger.info('=== 开始执行获取我的监护人列表接口 ===')
    openid = decoded.get('openid')
    user = query_user_by_openid(openid)
    if not user:
        return make_err_response({}, '用户不存在')

    try:
        relations = SupervisionRuleRelation.query.filter(
            SupervisionRuleRelation.solo_user_id == user.user_id,
            SupervisionRuleRelation.status == 2
        ).distinct(SupervisionRuleRelation.supervisor_user_id).all()

        guardians = []
        for rel in relations:
            sup = query_user_by_id(rel.supervisor_user_id)
            guardians.append({
                'user_id': sup.user_id,
                'nickname': sup.nickname,
                'avatar_url': sup.avatar_url
            })

        return make_succ_response({'guardians': guardians})
    except Exception as e:
        app.logger.error(f'获取我的监护人列表失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取我的监护人列表失败: {str(e)}')


@app.route('/api/rules/supervision/records', methods=['GET'])
@login_required
def get_supervised_checkin_records(decoded):
    """
    获取被监督用户的打卡记录接口
    """
    app.logger.info('=== 开始执行获取被监督用户打卡记录接口 ===')

    openid = decoded.get('openid')
    user = query_user_by_openid(openid)
    if not user:
        app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    try:
        # 获取查询参数
        params = request.args
        solo_user_id = params.get('solo_user_id')
        rule_id = params.get('rule_id')  # 可选：特定规则ID
        start_date_str = params.get(
            'start_date', (date.today() - timedelta(days=7)).strftime('%Y-%m-%d'))
        end_date_str = params.get(
            'end_date', date.today().strftime('%Y-%m-%d'))

        if not solo_user_id:
            return make_err_response({}, '缺少solo_user_id参数')

        # 解析日期
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

        # 检查是否有权限监督该用户或规则
        if rule_id:
            if not user.can_supervise_rule(int(rule_id)):
                return make_err_response({}, '无权限监督该规则')
        else:
            if not user.can_supervise_user(int(solo_user_id)):
                return make_err_response({}, '无权限监督该用户')

        # 根据是否有特定规则ID来查询打卡记录
        if rule_id:
            # 查询特定规则的打卡记录
            records = CheckinRecord.query.filter(
                CheckinRecord.solo_user_id == int(solo_user_id),
                CheckinRecord.rule_id == int(rule_id),
                CheckinRecord.planned_time >= datetime.combine(
                    start_date, time.min),
                CheckinRecord.planned_time <= datetime.combine(
                    end_date, time.max)
            ).order_by(CheckinRecord.planned_time.desc()).all()
        else:
            # 查询特定用户的所有可监督规则的打卡记录
            supervised_rules = user.get_supervised_rules(int(solo_user_id))
            rule_ids = [rule.rule_id for rule in supervised_rules]
            if not rule_ids:
                records = []
            else:
                records = CheckinRecord.query.filter(
                    CheckinRecord.solo_user_id == int(solo_user_id),
                    CheckinRecord.rule_id.in_(rule_ids),
                    CheckinRecord.planned_time >= datetime.combine(
                        start_date, time.min),
                    CheckinRecord.planned_time <= datetime.combine(
                        end_date, time.max)
                ).order_by(CheckinRecord.planned_time.desc()).all()

        # 转换为响应格式
        history_data = []
        for record in records:
            history_data.append({
                'record_id': record.record_id,
                'rule_id': record.rule_id,
                'rule_name': record.rule.rule_name,
                'icon_url': record.rule.icon_url,
                'planned_time': record.planned_time.strftime('%Y-%m-%d %H:%M:%S'),
                'checkin_time': record.checkin_time.strftime('%Y-%m-%d %H:%M:%S') if record.checkin_time else None,
                'status': record.status_name,  # 使用模型中的状态名称
                'created_at': record.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })

        response_data = {
            'start_date': start_date_str,
            'end_date': end_date_str,
            'history': history_data
        }

        app.logger.info(
            f'成功获取被监督用户打卡记录，监督者ID: {user.user_id}, 被监督者ID: {solo_user_id}, 记录数量: {len(history_data)}')
        return make_succ_response(response_data)

    except Exception as e:
        app.logger.error(f'获取被监督用户打卡记录时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取被监督用户打卡记录失败: {str(e)}')


@app.route('/api/auth/login_phone_code', methods=['POST'])
def login_phone_code():
    try:
        params = request.get_json() or {}
        phone = params.get('phone')
        code = params.get('code')
        if not phone or not code:
            return make_err_response({}, '缺少phone或code参数')
        if not _verify_sms_code(phone, 'login', code) and not _verify_sms_code(phone, 'register', code):
            return make_err_response({}, '验证码无效或已过期')
        phone_secret = os.getenv('PHONE_ENC_SECRET', 'default_secret')
        phone_hash = sha256(
            f"{phone_secret}:{phone}".encode('utf-8')).hexdigest()
        user = User.query.filter_by(phone_hash=phone_hash).first()
        if not user:
            return make_err_response({}, '用户不存在')
        if not user.nickname:
            user.nickname = _gen_phone_nickname()
            update_user_by_id(user)
        import datetime as dt
        token_payload = {'openid': user.wechat_openid, 'user_id': user.user_id,
                         'exp': dt.datetime.utcnow() + dt.timedelta(hours=2)}
        try:
            token_secret = get_token_secret()
        except ValueError as e:
            app.logger.error(f'获取TOKEN_SECRET失败: {str(e)}')
            return make_err_response({}, '服务器配置错误')
        token = jwt.encode(token_payload, token_secret, algorithm='HS256')
        refresh_token = secrets.token_urlsafe(32)
        user.refresh_token = refresh_token
        user.refresh_token_expire = datetime.now() + dt.timedelta(days=7)
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
        phone_secret = os.getenv('PHONE_ENC_SECRET', 'default_secret')
        phone_hash = sha256(
            f"{phone_secret}:{phone}".encode('utf-8')).hexdigest()
        user = User.query.filter_by(phone_hash=phone_hash).first()
        if not user or not user.password_hash or not user.password_salt:
            return make_err_response({}, '账号不存在或未设置密码')
        pwd_hash = sha256(
            f"{password}:{user.password_salt}".encode('utf-8')).hexdigest()
        if pwd_hash != user.password_hash:
            return make_err_response({}, '密码不正确')
        if not user.nickname:
            user.nickname = _gen_phone_nickname()
            update_user_by_id(user)
        import datetime as dt
        token_payload = {'openid': user.wechat_openid, 'user_id': user.user_id,
                         'exp': dt.datetime.utcnow() + dt.timedelta(hours=2)}
        try:
            token_secret = get_token_secret()
        except ValueError as e:
            app.logger.error(f'获取TOKEN_SECRET失败: {str(e)}')
            return make_err_response({}, '服务器配置错误')
        token = jwt.encode(token_payload, token_secret, algorithm='HS256')
        refresh_token = secrets.token_urlsafe(32)
        user.refresh_token = refresh_token
        user.refresh_token_expire = datetime.now() + dt.timedelta(days=7)
        update_user_by_id(user)
        _audit(user.user_id, 'login_phone_password', {'phone': phone})
        return make_succ_response({'token': token, 'refresh_token': refresh_token, 'user_id': user.user_id})
    except Exception as e:
        app.logger.error(f'密码登录失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'登录失败: {str(e)}')
