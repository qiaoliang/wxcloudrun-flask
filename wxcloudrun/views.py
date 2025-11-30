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
from wxcloudrun.controllers.user_controller import UserController, CheckinController, CommunityController, login_required

# 加载环境变量
load_dotenv()

# 初始化控制器
user_controller = UserController()
checkin_controller = CheckinController()
community_controller = CommunityController()


@app.route('/')
def index():
    """
    :return: 返回index页面
    """
    app.logger.info("主页访问")
    from flask import make_response
    response = make_response(render_template('index.html'))
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response


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
    首次登录：前端传code、avatarUrl、nickName
    非首次登录：前端仅传code
    :return: 登录结果
    """
    return user_controller.login()


@app.route('/api/user/profile', methods=['GET', 'POST'])
def user_profile():
    """
    用户信息接口，支持获取和更新用户信息
    GET: 获取用户信息
    POST: 更新用户信息
    """
    # 验证token
    decoded, error_response = BaseController.verify_token()
    if error_response:
        return error_response
    
    return user_controller.get_or_update_profile(decoded)





@app.route('/api/community/verify', methods=['POST'])
@login_required
def community_verify(decoded):
    """
    社区工作人员身份验证接口
    """
    return community_controller.community_verify(decoded)







@app.route('/api/checkin/today', methods=['GET'])
@login_required
def get_today_checkin_items(decoded):
    """
    获取用户今日打卡事项列表
    """
    return checkin_controller.get_today_checkin_items(decoded)


@app.route('/api/checkin', methods=['POST'])
@login_required
def perform_checkin(decoded):
    """
    执行打卡操作
    """
    return checkin_controller.perform_checkin(decoded)


@app.route('/api/checkin/cancel', methods=['POST'])
@login_required
def cancel_checkin(decoded):
    """
    撤销打卡操作（仅限30分钟内）
    """
    return checkin_controller.cancel_checkin(decoded)


@app.route('/api/checkin/history', methods=['GET'])
@login_required
def get_checkin_history(decoded):
    """
    获取打卡历史记录
    """
    return checkin_controller.get_checkin_history(decoded)


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
    return checkin_controller.manage_checkin_rules(decoded)


@app.route('/api/refresh_token', methods=['POST'])
def refresh_token():
    """
    刷新token接口，使用refresh token获取新的access token
    """
    return user_controller.refresh_token()


@app.route('/api/logout', methods=['POST'])
@login_required
def logout(decoded):
    """
    用户登出接口，清除refresh token
    """
    return user_controller.logout(decoded)


@app.errorhandler(404)
def handle_404(e):
    """
    处理404错误，确保API路径返回正确的错误格式
    """
    from flask import request
    # 检查是否是API请求
    if request.path.startswith('/api/'):
        app.logger.warning(f'API路径未找到: {request.path}')
        return make_err_response({}, 'API路径未找到'), 404
    # 对于非API路径，返回HTML页面
    return render_template('index.html'), 404


@app.errorhandler(500)
def handle_500(e):
    """
    处理500错误，确保返回JSON格式
    """
    from flask import request
    app.logger.error(f'服务器内部错误: {str(e)}', exc_info=True)
    # 检查是否是API请求
    if request.path.startswith('/api/'):
        return make_err_response({}, '服务器内部错误'), 500
    # 对于非API路径，返回HTML页面
    return render_template('index.html'), 500


