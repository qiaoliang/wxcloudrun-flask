"""
打卡功能视图模块（Controller 层）
负责参数验证、调用 Service 层、返回响应
"""

import logging
from datetime import datetime, date, timedelta
from flask import request
from wxcloudrun import app
from wxcloudrun.response import make_succ_response, make_err_response
from wxcloudrun.user_service import UserService
from wxcloudrun.checkin_rule_service import CheckinRuleService
from wxcloudrun.checkin_record_service import CheckinRecordService
from wxcloudrun.decorators import login_required
from wxcloudrun.utils.timeutil import parse_date_only,parse_time_only,format_time
app_logger = logging.getLogger('log')


@app.route('/api/checkin/today', methods=['GET'])
@login_required
def get_today_checkin_items(decoded):
    """
    获取用户今日打卡事项列表（Controller）
    """
    app.logger.info('=== 开始执行获取今日打卡事项接口 ===')

    # 参数验证
    openid = decoded.get('openid')
    user = UserService.query_user_by_openid(openid)
    if not user:
        app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    try:
        # 调用 Service 层获取今日打卡计划
        response_data = CheckinRuleService.get_today_checkin_plan(user.user_id)

        app.logger.info(
            f'成功获取今日打卡事项，用户ID: {user.user_id}, 事项数量: {len(response_data["checkin_items"])}')
        return make_succ_response(response_data)

    except Exception as e:
        app.logger.error(f'获取今日打卡事项时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取今日打卡事项失败: {str(e)}')


@app.route('/api/checkin', methods=['POST'])
@login_required
def perform_checkin(decoded):
    """
    执行打卡操作（Controller）
    支持个人规则和社区规则打卡
    """
    app.logger.info('=== 开始执行打卡接口 ===')

    # 参数验证 - 用户认证
    openid = decoded.get('openid')
    user = UserService.query_user_by_openid(openid)
    if not user:
        app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    try:
        # 参数验证 - 请求参数
        params = request.get_json()
        rule_id = params.get('rule_id')
        rule_source = params.get('rule_source', 'personal')  # 默认为个人规则
        
        if not rule_id:
            return make_err_response({}, '缺少rule_id参数')

        # 调用 Service 层执行打卡
        response_data = CheckinRecordService.perform_checkin(rule_id, user.user_id, rule_source)

        app.logger.info(f'用户 {user.user_id} 打卡成功，规则ID: {rule_id}')
        return make_succ_response(response_data)

    except ValueError as e:
        # 业务逻辑错误
        app.logger.warning(f'打卡失败: {str(e)}, 用户ID: {user.user_id}')
        return make_err_response({}, str(e))
    except Exception as e:
        # 系统错误
        app.logger.error(f'打卡时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'打卡失败: {str(e)}')


@app.route('/api/checkin/miss', methods=['POST'])
@login_required
def mark_missed(decoded):
    """
    标记当天规则为 missed（Controller）
    """
    app.logger.info('=== 开始执行标记miss接口 ===')

    # 参数验证 - 用户认证
    openid = decoded.get('openid')
    user = UserService.query_user_by_openid(openid)
    if not user:
        app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    try:
        # 参数验证 - 请求参数
        params = request.get_json() or {}
        rule_id = params.get('rule_id')
        if not rule_id:
            return make_err_response({}, '缺少rule_id参数')

        # 调用 Service 层标记 missed
        response_data = CheckinRecordService.mark_missed(rule_id, user.user_id)

        app.logger.info(f'用户 {user.user_id} 标记miss成功，规则ID: {rule_id}')
        return make_succ_response(response_data)

    except ValueError as e:
        # 业务逻辑错误
        app.logger.warning(f'标记miss失败: {str(e)}, 用户ID: {user.user_id}')
        return make_err_response({}, str(e))
    except Exception as e:
        # 系统错误
        app.logger.error(f'标记miss时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'标记miss失败: {str(e)}')


@app.route('/api/checkin/cancel', methods=['POST'])
@login_required
def cancel_checkin(decoded):
    """
    撤销打卡操作（Controller）
    """
    app.logger.info('=== 开始执行撤销打卡接口 ===')

    # 参数验证 - 用户认证
    openid = decoded.get('openid')
    user = UserService.query_user_by_openid(openid)
    if not user:
        app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    try:
        # 参数验证 - 请求参数
        params = request.get_json()
        record_id = params.get('record_id')
        if not record_id:
            return make_err_response({}, '缺少record_id参数')

        # 调用 Service 层撤销打卡
        response_data = CheckinRecordService.cancel_checkin(record_id, user.user_id)

        app.logger.info(f'用户 {user.user_id} 撤销打卡成功，记录ID: {record_id}')
        return make_succ_response(response_data)

    except ValueError as e:
        # 业务逻辑错误
        app.logger.warning(f'撤销打卡失败: {str(e)}, 用户ID: {user.user_id}')
        return make_err_response({}, str(e))
    except Exception as e:
        # 系统错误
        app.logger.error(f'撤销打卡时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'撤销打卡失败: {str(e)}')


@app.route('/api/checkin/history', methods=['GET'])
@login_required
def get_checkin_history(decoded):
    """
    获取打卡历史记录（Controller）
    """
    app.logger.info('=== 开始执行获取打卡历史接口 ===')

    # 参数验证 - 用户认证
    openid = decoded.get('openid')
    user = UserService.query_user_by_openid(openid)
    if not user:
        app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    try:
        # 参数验证 - 查询参数
        params = request.args
        start_date_str = params.get(
            'start_date', (date.today() - timedelta(days=7)).strftime('%Y-%m-%d'))
        end_date_str = params.get(
            'end_date', date.today().strftime('%Y-%m-%d'))

        # 解析日期
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

        # 调用 Service 层获取历史记录
        response_data = CheckinRecordService.get_checkin_history(
            user.user_id, start_date, end_date)

        app.logger.info(
            f'成功获取打卡历史，用户ID: {user.user_id}, 记录数量: {len(response_data["history"])}')
        return make_succ_response(response_data)

    except ValueError as e:
        # 参数验证错误
        app.logger.warning(f'获取打卡历史失败: {str(e)}, 用户ID: {user.user_id}')
        return make_err_response({}, str(e))
    except Exception as e:
        # 系统错误
        app.logger.error(f'获取打卡历史时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取打卡历史失败: {str(e)}')


@app.route('/api/checkin/rules', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def manage_checkin_rules(decoded):
    """
    打卡规则管理接口（Controller）
    GET: 获取打卡规则列表
    POST: 创建打卡规则
    PUT: 更新打卡规则
    DELETE: 删除打卡规则
    """
    app.logger.info(f'=== 开始执行打卡规则管理接口: {request.method} ===')

    # 参数验证 - 用户认证
    openid = decoded.get('openid')
    user = UserService.query_user_by_openid(openid)
    if not user:
        app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    try:
        if request.method == 'GET':
            # 获取用户的所有打卡规则
            rules = CheckinRuleService.query_rules_by_user_id(user.user_id)

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

            response_data = {'rules': rules_data}
            app.logger.info(
                f'成功获取打卡规则列表，用户ID: {user.user_id}, 规则数量: {len(rules_data)}')
            return make_succ_response(response_data)

        elif request.method == 'POST':
            # 参数验证
            params = request.get_json()
            if not params.get('rule_name'):
                app.logger.error('❌ 参数验证失败: 缺少rule_name参数')
                return make_err_response({}, '缺少rule_name参数')

            # 准备规则数据
            rule_data = {
                'rule_name': params['rule_name'],
                'icon_url': params.get('icon_url', ''),
                'frequency_type': params.get('frequency_type', 0),
                'time_slot_type': params.get('time_slot_type', 4),
                'custom_time': parse_time_only(params.get('custom_time')),
                'week_days': params.get('week_days', 127),
                'custom_start_date': parse_date_only(params.get('custom_start_date')),
                'custom_end_date': parse_date_only(params.get('custom_end_date')),
                'status': params.get('status', 1)
            }

            # 调用 Service 层创建规则
            new_rule = CheckinRuleService.create_rule(rule_data, user.user_id)

            response_data = {
                'rule_id': new_rule.rule_id,
                'message': '创建打卡规则成功'
            }
            app.logger.info(
                f'成功创建打卡规则，用户ID: {user.user_id}, 规则ID: {new_rule.rule_id}')
            return make_succ_response(response_data)

        elif request.method == 'PUT':
            # 参数验证
            params = request.get_json()
            rule_id = params.get('rule_id')
            if not rule_id:
                return make_err_response({}, '缺少rule_id参数')

            # 准备更新数据
            rule_data = {}
            if 'rule_name' in params:
                rule_data['rule_name'] = params['rule_name']
            if 'icon_url' in params:
                rule_data['icon_url'] = params['icon_url']
            if 'frequency_type' in params:
                rule_data['frequency_type'] = params['frequency_type']
            if 'time_slot_type' in params:
                rule_data['time_slot_type'] = params['time_slot_type']
            if 'custom_time' in params:
                rule_data['custom_time'] = parse_time_only(params['custom_time'])
            if 'week_days' in params:
                rule_data['week_days'] = params['week_days']
            if 'custom_start_date' in params:
                rule_data['custom_start_date'] = parse_date_only(params['custom_start_date'])
            if 'custom_end_date' in params:
                rule_data['custom_end_date'] = parse_date_only(params['custom_end_date'])
            if 'status' in params:
                rule_data['status'] = params['status']

            # 调用 Service 层更新规则
            updated_rule = CheckinRuleService.update_rule(rule_id, rule_data, user.user_id)

            response_data = {
                'rule_id': updated_rule.rule_id,
                'message': '更新打卡规则成功'
            }
            app.logger.info(
                f'成功更新打卡规则，用户ID: {user.user_id}, 规则ID: {rule_id}')
            return make_succ_response(response_data)

        elif request.method == 'DELETE':
            # 参数验证
            params = request.get_json()
            rule_id = params.get('rule_id')
            if not rule_id:
                return make_err_response({}, '缺少rule_id参数')

            # 调用 Service 层删除规则
            CheckinRuleService.delete_rule(rule_id, user.user_id)

            response_data = {
                'rule_id': rule_id,
                'message': '删除打卡规则成功'
            }
            app.logger.info(
                f'成功删除打卡规则，用户ID: {user.user_id}, 规则ID: {rule_id}')
            return make_succ_response(response_data)

    except ValueError as e:
        # 业务逻辑错误（如权限不足、数据验证失败）
        app.logger.warning(f'打卡规则管理失败: {str(e)}, 用户ID: {user.user_id}')
        return make_err_response({}, str(e))
    except Exception as e:
        # 系统错误
        app.logger.error(f'打卡规则管理时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'打卡规则管理失败: {str(e)}')