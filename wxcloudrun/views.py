from datetime import datetime
import requests
import jwt
import os
from dotenv import load_dotenv
from flask import render_template, request
from run import app
from wxcloudrun.dao import delete_counterbyid, query_counterbyid, insert_counter, update_counterbyid
from wxcloudrun.model import Counters
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
    counter = Counters.query.filter(Counters.id == 1).first()
    return make_succ_response(0) if counter is None else make_succ_response(counter.count)

@app.route('/api/login', methods=['GET'])
def login():
    """
    登录接口，通过code获取用户信息并返回token
    :return: token
    """
    # 获取URL查询参数
    code = request.args.get('code')
    if not code:
        return make_err_response('缺少code参数')
    # 在日志中打印code参数
    app.logger.info(f'login code: {code}')
    # 微信小程序配置
    appid = os.getenv('WX_APPID', 'your-appid')
    secret = os.getenv('WX_SECRET', 'your-secret')

    # 调用微信小程序code2Session API
    url = f'https://api.weixin.qq.com/sns/jscode2session?appid={appid}&secret={secret}&js_code={code}&grant_type=authorization_code'
    try:
        response = requests.get(url)
        data = response.json()
        # 在日志中打印API响应
        app.logger.info(f'login 微信API响应: {data}')

        # 检查API调用是否成功
        if 'errcode' in data and data['errcode'] != 0:
            return make_err_response(f'微信API调用失败: {data.get("errmsg", "未知错误")}')

        # 获取openid和session_key
        openid = data.get('openid')
        session_key = data.get('session_key')

        if not openid or not session_key:
            return make_err_response('获取用户信息失败')

        # 生成JWT token
        # 注意：实际项目中应该使用更安全的密钥，并设置合理的过期时间
        token_secret = os.getenv('TOKEN_SECRET', 'your-token-secret')
        token = jwt.encode(
            {
                'openid': openid,
                'session_key': session_key,
                'exp': datetime.now().timestamp() + 7 * 24 * 3600  # 7天过期
            },
            token_secret,
            algorithm='HS256'
        )
        # 在日志中打印token
        app.logger.info(f'login 返回 token: {token}')
        # 在日志中打印data参数
        app.logger.info(f'login 返回 data: {data}')

        # 返回token
        return make_succ_response({'token': token,"data":data})

    except Exception as e:
        return make_err_response(f'服务器错误: {str(e)}')
