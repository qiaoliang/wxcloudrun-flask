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
        return make_err_response('缺少请求体参数')
    
    code = params.get('code')
    if not code:
        return make_err_response('缺少code参数')
    # 在日志中打印code参数
    app.logger.info(f'login code: {code}')
            # 返回token
    return make_succ_response({'token': 'test_token'})

