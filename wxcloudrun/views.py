import logging
from flask import Flask, render_template, request
from flask_cors import CORS
import json
import time
from datetime import datetime, date, timedelta
import jwt
import requests
from functools import wraps
from dotenv import load_dotenv  # 添加缺失的导入
from wxcloudrun import db, app  # 从wxcloudrun导入app对象
from wxcloudrun.model import Counters, User, CheckinRule, CheckinRecord
from wxcloudrun.response import make_succ_empty_response, make_succ_response, make_err_response
from wxcloudrun.dao import *

# 加载环境变量
load_dotenv()


@app.route('/')
def index():
    """
    :return: 返回index页面
    """
    app.logger.info("主页访问")
    return render_template('index.html')


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
        return make_err_response({},'缺少请求体参数')

    app.logger.info('成功获取请求参数，开始检查code参数')

    code = params.get('code')
    if not code:
        app.logger.warning('登录请求缺少code参数')
        return make_err_response({},'缺少code参数')

    # 打印code用于调试
    app.logger.info(f'获取到的code: {code}')

    # 获取可能传递的用户信息
    nickname = params.get('nickname')
    avatar_url = params.get('avatar_url')

    app.logger.info(f'获取到的用户信息 - nickname: {nickname}, avatar_url: {avatar_url}')

    app.logger.info('开始调用微信API获取用户openid和session_key')

    # 调用微信API获取用户信息
    try:
        import config
        app.logger.info(f'从配置中获取WX_APPID: {config.WX_APPID[:10]}...' if hasattr(config, 'WX_APPID') and config.WX_APPID else 'WX_APPID未配置')
        app.logger.info(f'从配置中获取WX_SECRET: {config.WX_SECRET[:10]}...' if hasattr(config, 'WX_SECRET') and config.WX_SECRET else 'WX_SECRET未配置')

        wx_url = f'https://api.weixin.qq.com/sns/jscode2session?appid={config.WX_APPID}&secret={config.WX_SECRET}&js_code={code}&grant_type=authorization_code'
        app.logger.info(f'请求微信API的URL: {wx_url[:100]}...')  # 只打印URL前100个字符以避免敏感信息泄露

        # 发送请求到微信API，禁用SSL验证以解决证书问题（仅用于开发测试环境）
        app.logger.info('正在发送请求到微信API...')
        wx_response = requests.get(wx_url, timeout=30, verify=False)  # 增加超时时间到30秒
        app.logger.info(f'微信API响应状态码: {wx_response.status_code}')

        wx_data = wx_response.json()
        app.logger.info(f'微信API响应数据类型: {type(wx_data)}')
        app.logger.info(f'微信API响应内容: {wx_data}')

        # 检查微信API返回的错误
        if 'errcode' in wx_data:
            app.logger.error(f'微信API返回错误 - errcode: {wx_data.get("errcode")}, errmsg: {wx_data.get("errmsg")}')
            return make_err_response({}, f'微信API错误: {wx_data.get("errmsg", "未知错误")}')

        # 获取openid和session_key
        app.logger.info('正在从微信API响应中提取openid和session_key')
        openid = wx_data.get('openid')
        session_key = wx_data.get('session_key')

        app.logger.info(f'提取到的openid: {openid}')
        app.logger.info(f'提取到的session_key: {"*" * 10}')  # 隐藏session_key的实际值

        if not openid or not session_key:
            app.logger.error(f'微信API返回数据不完整 - openid存在: {bool(openid)}, session_key存在: {bool(session_key)}')
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

        # 临时使用硬编码的TOKEN_SECRET确保编码和解码使用相同的密钥
        token_secret = '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f'
        app.logger.info(f'使用的硬编码TOKEN_SECRET: {token_secret}')

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

    except requests.exceptions.Timeout as e:
        app.logger.error(f'请求微信API超时: {str(e)}')
        return make_err_response({}, f'调用微信API超时: {str(e)}')
    except requests.exceptions.RequestException as e:
        app.logger.error(f'请求微信API时发生网络错误: {str(e)}')
        return make_err_response({}, f'调用微信API失败: {str(e)}')
    except jwt.PyJWTError as e:
        app.logger.error(f'JWT处理错误: {str(e)}')
        return make_err_response({}, f'JWT处理失败: {str(e)}')
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
        'role': user.role_name,  # 返回用户角色名称
        'is_verified': user.verification_status == 2,  # 返回验证状态（仅对社区工作人员有意义）
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

    # 获取请求体参数
    params = request.get_json() if request.get_json() else {}
    app.logger.info(f'请求体参数: {params}')

    # 验证token
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        header_token = auth_header[7:]  # 去掉 'Bearer ' 前缀
    else:
        header_token = auth_header
    token = params.get('token') or header_token

    # 打印传入的token用于调试
    app.logger.info(f'从请求中获取的token: {token}')
    app.logger.info(f'Authorization header完整内容: {auth_header}')

    if not token:
        app.logger.warning('请求中缺少token参数')
        return make_err_response({}, '缺少token参数')

    try:
        # 解码token
        # 检查token是否包含额外的引号并去除
        if token and token.startswith('"') and token.endswith('"'):
            token = token[1:-1]  # 去除首尾的引号
            app.logger.info(f'检测到并去除了token的额外引号，处理后的token: {token[:50]}...')
        
        # 使用硬编码的TOKEN_SECRET确保编码和解码使用相同的密钥
        token_secret = '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f'
        app.logger.info(f'使用的硬编码TOKEN_SECRET: {token_secret}')
        app.logger.info(f'解码token: {token[:50]}...')  # 记录token前缀用于调试
        app.logger.info(f'使用的token secret: {token_secret[:]}')  # 记录secret前缀用于调试

        # 使用硬编码的TOKEN_SECRET进行解码，确保与编码时使用相同的密钥
        token_secret = '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f'
        app.logger.info(f'解码时使用的硬编码TOKEN_SECRET: {token_secret[:]}')  # 打印完整密钥用于调试

        # 解码token，启用过期验证
        decoded = jwt.decode(
            token,
            token_secret,
            algorithms=['HS256']
        )
        app.logger.info(f'解码后的payload: {decoded}')
        openid = decoded.get('openid')

        if not openid:
            app.logger.error('解码后的token中未找到openid')
            return make_err_response({}, 'token无效')

        # 根据HTTP方法决定操作
        if request.method == 'GET':
            app.logger.info(f'GET请求 - 查询用户信息，openid: {openid}')
            # 查询用户信息
            user = query_user_by_openid(openid)
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
                'status': user.status_name  # 返回字符串形式的状态名
            }

            app.logger.info(f'成功查询到用户信息，用户ID: {user.user_id}')
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

            app.logger.info(f'待更新的用户信息 - nickname: {nickname}, avatar_url: {avatar_url}, phone_number: {phone_number}, role: {role}')

            # 更新用户信息到数据库
            if nickname is not None:
                app.logger.info(f'更新nickname: {user.nickname} -> {nickname}')
                user.nickname = nickname
            if avatar_url is not None:
                app.logger.info(f'更新avatar_url: {user.avatar_url} -> {avatar_url}')
                user.avatar_url = avatar_url
            if phone_number is not None:
                app.logger.info(f'更新phone_number: {user.phone_number} -> {phone_number}')
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
            if community_id is not None:
                app.logger.info(f'更新community_id: {user.community_id} -> {community_id}')
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
                    app.logger.info(f'token header解码成功: {header_decoded.decode("utf-8")}')
                except Exception as decode_err:
                    app.logger.error(f'token header解码失败: {str(decode_err)}')
        return make_err_response({}, 'token格式错误')
    except jwt.InvalidTokenError as e:
        app.logger.error(f'token无效: {str(e)}')
        return make_err_response({}, 'token无效')
    except Exception as e:
        app.logger.error(f'JWT处理时发生未知错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'JWT处理失败: {str(e)}')
    except Exception as e:
        app.logger.error(f'处理用户信息时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'处理用户信息失败: {str(e)}')

    app.logger.info('=== 用户信息接口执行完成 ===')


# 辅助函数：验证JWT token
def verify_token():
    """
    验证JWT token并返回解码后的用户信息
    """
    # 获取请求体参数
    params = request.get_json() if request.get_json() else {}
    
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

    try:
        # 使用硬编码的TOKEN_SECRET进行解码
        token_secret = '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f'
        
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


def login_required(f):
    """
    统一的登录认证装饰器
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        decoded, error_response = verify_token()
        if error_response:
            return error_response
        # 将解码后的用户信息传递给被装饰的函数
        return f(decoded, *args, **kwargs)
    return decorated_function


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
                today_records = query_checkin_records_by_rule_id_and_date(rule.rule_id, today)
                
                # 计算计划打卡时间
                if rule.time_slot_type == 4 and rule.custom_time:  # 自定义时间
                    planned_time = datetime.combine(today, rule.custom_time)
                elif rule.time_slot_type == 1:  # 上午
                    planned_time = datetime.combine(today, time(9, 0))  # 默认上午9点
                elif rule.time_slot_type == 2:  # 下午
                    planned_time = datetime.combine(today, time(14, 0))  # 默认下午2点
                else:  # 晚上，默认晚上8点
                    planned_time = datetime.combine(today, time(20, 0))
                
                # 确定打卡状态
                checkin_status = 'unchecked'
                checkin_time = None
                record_id = None
                
                for record in today_records:
                    if record.status == 1:  # 已打卡
                        checkin_status = 'checked'
                        checkin_time = record.checkin_time.strftime('%H:%M:%S') if record.checkin_time else None
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
        
        app.logger.info(f'成功获取今日打卡事项，用户ID: {user.user_id}, 事项数量: {len(checkin_items)}')
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
        existing_records = query_checkin_records_by_rule_id_and_date(rule_id, today)
        
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
        start_date_str = params.get('start_date', (date.today() - timedelta(days=7)).strftime('%Y-%m-%d'))
        end_date_str = params.get('end_date', date.today().strftime('%Y-%m-%d'))
        
        # 解析日期
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # 获取打卡记录
        records = query_checkin_records_by_user_and_date_range(user.user_id, start_date, end_date)
        
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
        
        app.logger.info(f'成功获取打卡历史，用户ID: {user.user_id}, 记录数量: {len(history_data)}')
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
                    'custom_time': rule.custom_time.strftime('%H:%M:%S') if rule.custom_time else None,
                    'week_days': rule.week_days,
                    'status': rule.status,
                    'created_at': rule.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_at': rule.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                })
            
            response_data = {
                'rules': rules_data
            }
            
            app.logger.info(f'成功获取打卡规则列表，用户ID: {user.user_id}, 规则数量: {len(rules_data)}')
            return make_succ_response(response_data)
            
        elif request.method == 'POST':
            # 创建打卡规则
            params = request.get_json()
            
            rule_name = params.get('rule_name')
            if not rule_name:
                return make_err_response({}, '缺少rule_name参数')
            
            # 创建新的打卡规则
            new_rule = CheckinRule(
                solo_user_id=user.user_id,
                rule_name=rule_name,
                icon_url=params.get('icon_url', ''),
                frequency_type=params.get('frequency_type', 0),  # 默认每天
                time_slot_type=params.get('time_slot_type', 4),  # 默认自定义时间
                custom_time=datetime.strptime(params['custom_time'], '%H:%M:%S').time() if params.get('custom_time') else None,
                week_days=params.get('week_days', 127),  # 默认周一到周日
                status=params.get('status', 1)  # 默认启用
            )
            
            insert_checkin_rule(new_rule)
            
            response_data = {
                'rule_id': new_rule.rule_id,
                'message': '创建打卡规则成功'
            }
            
            app.logger.info(f'成功创建打卡规则，用户ID: {user.user_id}, 规则ID: {new_rule.rule_id}')
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
                rule.custom_time = datetime.strptime(params['custom_time'], '%H:%M:%S').time() if params['custom_time'] else None
            if 'week_days' in params:
                rule.week_days = params['week_days']
            if 'status' in params:
                rule.status = params['status']
            
            update_checkin_rule_by_id(rule)
            
            response_data = {
                'rule_id': rule.rule_id,
                'message': '更新打卡规则成功'
            }
            
            app.logger.info(f'成功更新打卡规则，用户ID: {user.user_id}, 规则ID: {rule.rule_id}')
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
            
            delete_checkin_rule_by_id(rule_id)
            
            response_data = {
                'rule_id': rule_id,
                'message': '删除打卡规则成功'
            }
            
            app.logger.info(f'成功删除打卡规则，用户ID: {user.user_id}, 规则ID: {rule_id}')
            return make_succ_response(response_data)
            
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
        token_secret = '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f'
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
        user = session.query(User).filter(User.refresh_token == refresh_token).first()
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


