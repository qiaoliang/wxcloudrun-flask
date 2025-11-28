from datetime import datetime
import requests
import jwt
import os
from dotenv import load_dotenv
from flask import render_template, request
from wxcloudrun import app
from wxcloudrun.dao import delete_counterbyid, query_counterbyid, insert_counter, update_counterbyid, query_user_by_openid, insert_user, update_user_by_id
from wxcloudrun.model import Counters, User
from wxcloudrun.response import make_succ_empty_response, make_succ_response, make_err_response

# 加载环境变量
load_dotenv()


@app.route('/')
def index():
    """
    :return: 返回index页面
    """
    return render_template('index.html')


@app.route('/api/count', methods=['POST'])
def count():
    """
    :return:计数结果/清除结果
    """

    # 获取请求体参数
    params = request.get_json()

    # 检查action参数
    if 'action' not in params:
        return make_err_response('缺少action参数')

    # 按照不同的action的值，进行不同的操作
    action = params['action']

    # 执行自增操作
    if action == 'inc':
        counter = query_counterbyid(1)
        if counter is None:
            counter = Counters()
            counter.id = 1
            counter.count = 1
            counter.created_at = datetime.now()
            counter.updated_at = datetime.now()
            insert_counter(counter)
        else:
            counter.id = 1
            counter.count += 1
            counter.updated_at = datetime.now()
            update_counterbyid(counter)
        return make_succ_response(counter.count)

    # 执行清0操作
    elif action == 'clear':
        delete_counterbyid(1)
        return make_succ_empty_response()

    # action参数错误
    else:
        return make_err_response('action参数错误')


@app.route('/api/count', methods=['GET'])
def get_count():
    """
    :return: 计数的值
    """
    counter = query_counterbyid(1)
    return make_succ_response(0) if counter is None else make_succ_response(counter.count)

@app.route('/api/login', methods=['POST'])
def login():
    """
    登录接口，通过code获取用户信息并返回token
    :return: token
    """
    # 在日志中打印登录请求
    app.logger.info(f'login 请求参数: {request.get_json()}')
    # 获取请求体参数
    params = request.get_json()
    if not params:
        return make_err_response({},'缺少请求体参数')

    code = params.get('code')
    if not code:
        return make_err_response({},'缺少code参数')
    
    # 打印code用于调试
    app.logger.info(f'login code: {code}')
        
    # 获取可能传递的用户信息
    nickname = params.get('nickname')
    avatar_url = params.get('avatar_url')
    
    # 在日志中打印code参数
    app.logger.info(f'login code: {code}')

    # 调用微信API获取用户信息
    try:
        import config
        wx_url = f'https://api.weixin.qq.com/sns/jscode2session?appid={config.WX_APPID}&secret={config.WX_SECRET}&js_code={code}&grant_type=authorization_code'

        # 发送请求到微信API，禁用SSL验证以解决证书问题（仅用于开发测试环境）
        wx_response = requests.get(wx_url, timeout=10, verify=False)
        wx_data = wx_response.json()

        app.logger.info(f'微信API响应: {wx_data}')

        # 检查微信API返回的错误
        if 'errcode' in wx_data:
            app.logger.error(f'微信API返回错误: {wx_data}')
            return make_err_response({}, f'微信API错误: {wx_data.get("errmsg", "未知错误")}')

        # 获取openid和session_key
        openid = wx_data.get('openid')
        session_key = wx_data.get('session_key')

        if not openid or not session_key:
            app.logger.error(f'微信API返回数据不完整: {wx_data}')
            return make_err_response({}, '微信API返回数据不完整')

        # 检查用户是否已存在
        existing_user = query_user_by_openid(openid)
        is_new = not bool(existing_user)
        
        if not existing_user:
            # 创建新用户
            user = User(
                wechat_openid=openid,
                nickname=nickname,
                avatar_url=avatar_url,
                role=1,  # 默认为独居者角色
                status=1  # 默认为正常状态
            )
            insert_user(user)
            app.logger.info(f'新用户创建成功，openid: {openid}')
        else:
            # 更新现有用户信息（如果提供了新的头像或昵称）
            user = existing_user
            updated = False
            if nickname and user.nickname != nickname:
                user.nickname = nickname
                updated = True
            if avatar_url and user.avatar_url != avatar_url:
                user.avatar_url = avatar_url
                updated = True
            if updated:
                update_user_by_id(user)
                app.logger.info(f'用户信息更新成功，openid: {openid}')

        # 生成JWT token
        token_payload = {
            'openid': openid,
            'session_key': session_key
        }
        token = jwt.encode(token_payload, os.environ.get('TOKEN_SECRET', 'your-secret-key'), algorithm='HS256')
        
        # 打印生成的token用于调试
        app.logger.info(f'生成的token: {token}')
    except Exception as e:
        app.logger.error(f'调用微信API时发生错误: {str(e)}')
        return make_err_response({}, f'调用微信API失败: {str(e)}')

    # 构造返回数据，包含用户的 token
    response_data = {
        'token': token,
        'user_id': user.user_id,
        'is_new_user': is_new  # 标识是否为新用户
    }
    # 返回自定义格式的响应
    return make_succ_response(response_data)


@app.route('/api/user/profile', methods=['GET', 'POST'])
def user_profile():
    """
    用户信息接口，支持获取和更新用户信息
    GET: 获取用户信息
    POST: 更新用户信息
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
    
    # 打印传入的token用于调试
    app.logger.info(f'收到的token: {token}')
    app.logger.info(f'Authorization header: {auth_header}')
    
    if not token:
        return make_err_response({}, '缺少token参数')

    try:
        # 解码token
        token_secret = os.environ.get('TOKEN_SECRET', 'your-secret-key')
        app.logger.info(f'解码token: {token[:50]}... (前50字符)')  # 记录token前缀用于调试
        app.logger.info(f'使用的token secret: {token_secret[:10]}... (前10字符)')  # 记录secret前缀用于调试
        decoded = jwt.decode(token, token_secret, algorithms=['HS256'])
        app.logger.info(f'解码后的payload: {decoded}')
        openid = decoded.get('openid')

        if not openid:
            return make_err_response({}, 'token无效')

        # 根据HTTP方法决定操作
        if request.method == 'GET':
            # 查询用户信息
            user = query_user_by_openid(openid)
            if not user:
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
            
            return make_succ_response(user_data)

        elif request.method == 'POST':
            # 查询用户
            user = query_user_by_openid(openid)
            if not user:
                return make_err_response({}, '用户不存在')

            # 获取可更新的用户信息（只更新非空字段）
            nickname = params.get('nickname')
            avatar_url = params.get('avatar_url')
            phone_number = params.get('phone_number')
            role = params.get('role')
            community_id = params.get('community_id')
            status = params.get('status')

            # 更新用户信息到数据库
            if nickname is not None:
                user.nickname = nickname
            if avatar_url is not None:
                user.avatar_url = avatar_url
            if phone_number is not None:
                user.phone_number = phone_number
            if role is not None:
                # 如果传入的是字符串，转换为对应的整数值
                if isinstance(role, str):
                    role_value = User.get_role_value(role)
                    if role_value is not None:
                        user.role = role_value
                elif isinstance(role, int):
                    user.role = role
            if community_id is not None:
                user.community_id = community_id
            if status is not None:
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

    except jwt.ExpiredSignatureError:
        app.logger.error('token已过期')
        return make_err_response({}, 'token已过期')
    except jwt.InvalidTokenError as e:
        app.logger.error(f'token无效: {str(e)}')
        return make_err_response({}, 'token无效')
    except Exception as e:
        app.logger.error(f'处理用户信息时发生错误: {str(e)}')
        return make_err_response({}, f'处理用户信息失败: {str(e)}')


