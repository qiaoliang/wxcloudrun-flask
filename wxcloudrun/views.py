import logging
from flask import Flask, render_template, request, g
import json
import time
from datetime import datetime, date, timedelta
import jwt
import requests
from functools import wraps
from dotenv import load_dotenv  # 添加缺失的导入
from wxcloudrun import db, app  # 从wxcloudrun导入app对象
from wxcloudrun.model import Counters, User, CheckinRule, CheckinRecord, RuleSupervision
from wxcloudrun.response import make_succ_empty_response, make_succ_response, make_err_response
from wxcloudrun.dao import *
from wxcloudrun.controllers.user_controller import UserController, CheckinController, CommunityController, login_required
from wxcloudrun.controllers.user_controller import BaseController
from wxcloudrun.services.phone_auth_service import get_phone_auth_service

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


# ==================== 监护关系相关API ====================

@app.route('/api/users/search', methods=['GET'])
@login_required
def search_users(decoded):
    """
    根据昵称搜索用户
    请求参数:
    - nickname: 搜索关键词
    - limit: 返回结果数量限制（默认10）
    """
    try:
        nickname = request.args.get('nickname', '').strip()
        limit = min(int(request.args.get('limit', 10)), 50)  # 最大限制50条
        
        if not nickname or len(nickname) < 2:
            return make_succ_response({
                'users': []
            })
        
        # 搜索用户，优先返回监护人
        users = User.query.filter(
            User.nickname.contains(nickname),
            User.status == 1,  # 只搜索正常状态的用户
            User.user_id != g.current_user.user_id  # 排除自己
        ).order_by(
            User.is_supervisor.desc(),  # 监护人优先
            User.nickname.asc()  # 昵称排序
        ).limit(limit).all()
        
        result = []
        for user in users:
            result.append({
                'user_id': user.user_id,
                'nickname': user.nickname,
                'avatar_url': user.avatar_url,
                'is_supervisor': user.is_supervisor,
                'permissions': user.permissions
            })
        
        app.logger.info(f"search_users: 搜索关键词 '{nickname}' 返回 {len(result)} 个结果")
        return make_succ_response({
            'users': result
        })
        
    except Exception as e:
        app.logger.error(f"search_users error: {str(e)}")
        return make_err_response("搜索用户失败")


@app.route('/api/rules/supervision/invite', methods=['POST'])
@login_required
def invite_supervisor(decoded):
    """
    为指定打卡规则邀请监护人
    请求参数:
    - rule_id: 打卡规则ID
    - supervisor_user_id: 监护人用户ID
    - invitation_message: 邀请消息（可选）
    """
    try:
        data = request.get_json()
        rule_id = data.get('rule_id')
        supervisor_user_id = data.get('supervisor_user_id')
        invitation_message = data.get('invitation_message', '')
        
        if not rule_id or not supervisor_user_id:
            return make_err_response("参数不完整")
        
        # 验证权限：只有规则创建者才能邀请监护人
        rule = CheckinRule.query.filter_by(rule_id=rule_id).first()
        if not rule:
            return make_err_response("打卡规则不存在")
        
        if rule.solo_user_id != g.current_user.user_id:
            return make_err_response("只有规则创建者才能邀请监护人")
        
        # 不能邀请自己
        if supervisor_user_id == g.current_user.user_id:
            return make_err_response("不能邀请自己作为监护人")
        
        # 检查是否已存在监护关系
        existing = check_existing_supervision(rule_id, supervisor_user_id)
        if existing:
            if existing.status == 1:
                return make_err_response("该用户已经是此规则的监护人")
            elif existing.status == 0:
                return make_err_response("已向该用户发送邀请，请等待响应")
        
        # 检查监护人数量限制
        supervisor_count = get_supervisor_count(rule_id)
        if supervisor_count >= 5:
            return make_err_response("一个规则最多只能有5个监护人")
        
        # 验证被邀请用户存在且是监护人
        supervisor_user = User.query.filter_by(
            user_id=supervisor_user_id, 
            status=1
        ).first()
        if not supervisor_user:
            return make_err_response("被邀请用户不存在")
        
        if not supervisor_user.is_supervisor:
            return make_err_response("被邀请用户不是监护人")
        
        # 创建监护关系
        supervision = create_rule_supervision(
            rule_id=rule_id,
            solo_user_id=rule.solo_user_id,
            supervisor_user_id=supervisor_user_id,
            invitation_message=invitation_message,
            invited_by_user_id=g.current_user.user_id
        )
        
        if not supervision:
            return make_err_response("创建邀请失败")
        
        # TODO: 发送通知给监护人
        
        app.logger.info(f"invite_supervisor: 用户 {g.current_user.user_id} 邀请 {supervisor_user_id} 监护规则 {rule_id}")
        return make_succ_response({
            'rule_supervision_id': supervision.rule_supervision_id,
            'status': supervision.status,
            'message': '邀请已发送'
        })
        
    except Exception as e:
        app.logger.error(f"invite_supervisor error: {str(e)}")
        return make_err_response("邀请失败")


@app.route('/api/supervision/invitations', methods=['GET'])
@login_required
def get_invitations(decoded):
    """
    获取用户的邀请列表
    请求参数:
    - type: 邀请类型 'received'(收到的) 或 'sent'(发出的)，默认received
    """
    try:
        invitation_type = request.args.get('type', 'received')
        status = request.args.get('status', None)  # 可选的状态过滤
        
        if status is not None:
            try:
                status = int(status)
            except ValueError:
                status = None
        
        supervisions = get_user_supervisions(
            g.current_user.user_id, 
            invitation_type, 
            status
        )
        
        result = []
        for supervision in supervisions:
            supervision_data = {
                'rule_supervision_id': supervision.rule_supervision_id,
                'status': supervision.status,
                'status_name': supervision.status_name,
                'invitation_message': supervision.invitation_message,
                'created_at': supervision.created_at.isoformat() if supervision.created_at else None,
                'responded_at': supervision.responded_at.isoformat() if supervision.responded_at else None
            }
            
            # 添加规则信息
            supervision_data['rule'] = {
                'rule_id': supervision.rule.rule_id,
                'rule_name': supervision.rule.rule_name,
                'icon_url': supervision.rule.icon_url,
                'solo_user': {
                    'user_id': supervision.solo_user.user_id,
                    'nickname': supervision.solo_user.nickname,
                    'avatar_url': supervision.solo_user.avatar_url
                }
            }
            
            # 添加邀请人信息
            supervision_data['invited_by'] = {
                'user_id': supervision.invited_by.user_id,
                'nickname': supervision.invited_by.nickname,
                'avatar_url': supervision.invited_by.avatar_url
            }
            
            result.append(supervision_data)
        
        app.logger.info(f"get_invitations: 用户 {g.current_user.user_id} {invitation_type} 类型邀请 {len(result)} 条")
        return make_succ_response({
            'invitations': result
        })
        
    except Exception as e:
        app.logger.error(f"get_invitations error: {str(e)}")
        return make_err_response("获取邀请列表失败")


@app.route('/api/supervision/respond', methods=['POST'])
@login_required
def respond_invitation(decoded):
    """
    响应监护邀请
    请求参数:
    - rule_supervision_id: 监护关系ID
    - action: 'accept' 或 'reject'
    - response_message: 响应消息（可选）
    """
    try:
        data = request.get_json()
        supervision_id = data.get('rule_supervision_id')
        action = data.get('action')
        response_message = data.get('response_message', '')
        
        if not supervision_id or not action:
            return make_err_response("参数不完整")
        
        if action not in ['accept', 'reject']:
            return make_err_response("操作类型无效")
        
        # 获取监护关系
        supervision = get_rule_supervision_by_id(supervision_id)
        if not supervision:
            return make_err_response("邀请不存在")
        
        # 验证权限：只有被邀请的监护人才能响应
        if supervision.supervisor_user_id != g.current_user.user_id:
            return make_err_response("无权限操作此邀请")
        
        # 验证状态：只能响应待确认的邀请
        if supervision.status != 0:
            return make_err_response("邀请已被处理")
        
        # 更新状态
        new_status = 1 if action == 'accept' else 2
        updated_supervision = update_supervision_status(
            supervision_id, 
            new_status, 
            response_message
        )
        
        if not updated_supervision:
            return make_err_response("响应失败")
        
        # TODO: 发送通知给邀请人
        
        status_text = "同意" if action == 'accept' else "拒绝"
        app.logger.info(f"respond_invitation: 用户 {g.current_user.user_id} {status_text} 邀请 {supervision_id}")
        return make_succ_response({
            'status': new_status,
            'message': f'已{status_text}邀请'
        })
        
    except Exception as e:
        app.logger.error(f"respond_invitation error: {str(e)}")
        return make_err_response("响应失败")


@app.route('/api/rules/supervision/list', methods=['GET'])
@login_required
def get_rule_supervisions_api(decoded):
    """
    获取指定规则的监护关系列表
    请求参数:
    - rule_id: 打卡规则ID
    """
    try:
        rule_id = request.args.get('rule_id')
        if not rule_id:
            return make_err_response("规则ID不能为空")
        
        # 验证权限：只有规则创建者可以查看监护关系
        rule = CheckinRule.query.filter_by(rule_id=rule_id).first()
        if not rule:
            return make_err_response("打卡规则不存在")
        
        if rule.solo_user_id != g.current_user.user_id:
            return make_err_response("无权限查看此规则的监护关系")
        
        supervisions = get_rule_supervisions(rule_id)
        
        result = []
        for supervision in supervisions:
            result.append({
                'rule_supervision_id': supervision.rule_supervision_id,
                'supervisor': {
                    'user_id': supervision.supervisor_user.user_id,
                    'nickname': supervision.supervisor_user.nickname,
                    'avatar_url': supervision.supervisor_user.avatar_url
                },
                'status': supervision.status,
                'status_name': supervision.status_name,
                'created_at': supervision.created_at.isoformat() if supervision.created_at else None
            })
        
        return make_succ_response({
            'supervisions': result
        })
        
    except Exception as e:
        app.logger.error(f"get_rule_supervisions_api error: {str(e)}")
        return make_err_response("获取监护关系列表失败")


@app.route('/api/supervisor/rules', methods=['GET'])
@login_required
def get_supervisor_rules(decoded):
    """
    获取监护人负责的所有规则
    """
    try:
        # 验证用户是监护人
        if not g.current_user.is_supervisor:
            return make_err_response("您不是监护人")
        
        supervised_rules = get_supervisor_active_rules(g.current_user.user_id)
        
        return make_succ_response({
            'supervised_rules': supervised_rules
        })
        
    except Exception as e:
        app.logger.error(f"get_supervisor_rules error: {str(e)}")
        return make_err_response("获取监护规则失败")


# ==================== 手机认证相关API ====================

@app.route('/api/send_sms', methods=['POST'])
def send_sms():
    """
    发送短信验证码
    请求参数:
    - phone: 手机号码
    """
    try:
        data = request.get_json()
        phone = data.get('phone', '').strip()
        
        if not phone:
            return make_err_response("手机号码不能为空")
        
        phone_auth_service = get_phone_auth_service()
        success, message, code = phone_auth_service.send_verification_code(phone)
        
        if success:
            # 在开发/测试环境中返回验证码
            response_data = {'message': message}
            if app.config.get('ENV') == 'development' or app.config.get('TESTING'):
                response_data['verification_code'] = code
            return make_succ_response(response_data)
        else:
            return make_err_response(message)
            
    except Exception as e:
        app.logger.error(f"send_sms error: {str(e)}")
        return make_err_response("发送验证码失败")


@app.route('/api/login_phone', methods=['POST'])
def login_phone():
    """
    手机号登录接口
    支持密码登录和短信验证码登录
    请求参数:
    - phone: 手机号码
    - password: 密码（密码登录时使用）
    - code: 短信验证码（短信登录时使用）
    - login_type: 登录类型 'password' 或 'sms'
    """
    try:
        data = request.get_json()
        phone = data.get('phone', '').strip()
        login_type = data.get('login_type', 'sms')
        
        if not phone:
            return make_err_response("手机号码不能为空")
        
        if login_type not in ['password', 'sms']:
            return make_err_response("登录类型无效")
        
        phone_auth_service = get_phone_auth_service()
        
        if login_type == 'password':
            password = data.get('password', '')
            if not password:
                return make_err_response("密码不能为空")
            success, message, user_info = phone_auth_service.login_with_password(phone, password)
        else:  # sms login
            code = data.get('code', '')
            if not code:
                return make_err_response("验证码不能为空")
            success, message, user_info = phone_auth_service.login_with_sms(phone, code)
        
        if success:
            return make_succ_response(user_info)
        else:
            return make_err_response(message)
            
    except Exception as e:
        app.logger.error(f"login_phone error: {str(e)}")
        return make_err_response("登录失败")


@app.route('/api/register_phone', methods=['POST'])
def register_phone():
    """
    手机号注册接口
    请求参数:
    - phone: 手机号码
    - code: 短信验证码
    - nickname: 用户昵称（可选）
    - avatar_url: 用户头像URL（可选）
    """
    try:
        data = request.get_json()
        phone = data.get('phone', '').strip()
        code = data.get('code', '').strip()
        nickname = data.get('nickname', '').strip()
        avatar_url = data.get('avatar_url', '').strip()
        
        if not phone or not code:
            return make_err_response("手机号码和验证码不能为空")
        
        phone_auth_service = get_phone_auth_service()
        success, message, user_info = phone_auth_service.verify_code_and_register(
            phone, code, nickname, avatar_url
        )
        
        if success:
            return make_succ_response(user_info)
        else:
            return make_err_response(message)
            
    except Exception as e:
        app.logger.error(f"register_phone error: {str(e)}")
        return make_err_response("注册失败")


@app.route('/api/set_password', methods=['POST'])
@login_required
def set_password(decoded):
    """
    设置密码接口
    请求参数:
    - password: 新密码
    """
    try:
        data = request.get_json()
        password = data.get('password', '').strip()
        
        if not password:
            return make_err_response("密码不能为空")
        
        if len(password) < 8:
            return make_err_response("密码长度至少8位")
        
        phone_auth_service = get_phone_auth_service()
        success, message = phone_auth_service.set_password(g.current_user.user_id, password)
        
        if success:
            return make_succ_response({'message': message})
        else:
            return make_err_response(message)
            
    except Exception as e:
        app.logger.error(f"set_password error: {str(e)}")
        return make_err_response("设置密码失败")


