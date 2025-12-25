"""
打卡功能模块路由
负责参数验证、调用 Service 层、返回响应
"""

import logging
from datetime import datetime, date, timedelta
from flask import request, current_app
from . import checkin_bp
from app.shared import make_succ_response, make_err_response
from app.shared.decorators import login_required
from app.shared.utils.auth import verify_token
from wxcloudrun.user_service import UserService
from wxcloudrun.checkin_rule_service import CheckinRuleService
from wxcloudrun.checkin_record_service import CheckinRecordService
from wxcloudrun.utils.timeutil import parse_date_only, parse_time_only, format_time

app_logger = logging.getLogger('log')


def _rule_to_dict(rule):
    """
    将规则对象转换为字典
    :param rule: CheckinRule 对象
    :return: 字典格式的规则数据
    """
    return {
        'rule_id': rule.rule_id,
        'user_id': rule.user_id,
        'community_id': rule.community_id,
        'rule_type': rule.rule_type,
        'rule_name': rule.rule_name,
        'icon_url': rule.icon_url,
        'frequency_type': rule.frequency_type,
        'time_slot_type': rule.time_slot_type,
        'custom_time': rule.custom_time.isoformat() if rule.custom_time else None,
        'week_days': rule.week_days,
        'custom_start_date': rule.custom_start_date.isoformat() if rule.custom_start_date else None,
        'custom_end_date': rule.custom_end_date.isoformat() if rule.custom_end_date else None,
        'status': rule.status,
        'created_at': rule.created_at.strftime('%Y-%m-%d %H:%M:%S') if rule.created_at else None,
        'updated_at': rule.updated_at.strftime('%Y-%m-%d %H:%M:%S') if rule.updated_at else None
    }


@checkin_bp.route('/checkin/today', methods=['GET'])
def get_today_checkin_items():
    """
    获取用户今日打卡事项列表（Controller）
    """
    current_app.logger.info('=== 开始执行获取今日打卡事项接口 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    # 参数验证
    openid = decoded.get('openid')
    user = UserService.query_user_by_openid(openid)
    if not user:
        current_app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    try:
        # 调用 Service 层获取今日打卡计划
        response_data = CheckinRuleService.get_today_checkin_plan(user.user_id)

        current_app.logger.info(
            f'成功获取今日打卡事项，用户ID: {user.user_id}, 事项数量: {len(response_data["checkin_items"])}')
        return make_succ_response(response_data)

    except Exception as e:
        current_app.logger.error(f'获取今日打卡事项时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取今日打卡事项失败: {str(e)}')


@checkin_bp.route('/checkin', methods=['POST'])
def perform_checkin():
    """
    执行打卡操作（Controller）
    """
    current_app.logger.info('=== 开始执行打卡操作接口 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    # 参数验证
    openid = decoded.get('openid')
    user = UserService.query_user_by_openid(openid)
    if not user:
        current_app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    # 获取请求参数
    params = request.get_json()
    if not params:
        current_app.logger.warning('打卡请求缺少请求体参数')
        return make_err_response({}, '缺少请求参数')

    rule_id = params.get('rule_id')
    checkin_time_str = params.get('checkin_time')
    note = params.get('note', '')

    if not rule_id:
        current_app.logger.warning('打卡请求缺少rule_id参数')
        return make_err_response({}, '缺少规则ID参数')

    if not checkin_time_str:
        current_app.logger.warning('打卡请求缺少checkin_time参数')
        return make_err_response({}, '缺少打卡时间参数')

    try:
        # 解析打卡时间
        checkin_time = parse_time_only(checkin_time_str)
        if not checkin_time:
            current_app.logger.error(f'打卡时间格式错误: {checkin_time_str}')
            return make_err_response({}, '打卡时间格式错误')

        # 调用 Service 层执行打卡
        response_data = CheckinRecordService.perform_checkin(
            user.user_id, rule_id, checkin_time, note
        )

        current_app.logger.info(
            f'用户 {user.user_id} 成功打卡，规则ID: {rule_id}, 打卡时间: {checkin_time_str}')
        return make_succ_response(response_data)

    except Exception as e:
        current_app.logger.error(f'执行打卡操作时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'打卡失败: {str(e)}')


@checkin_bp.route('/checkin/miss', methods=['POST'])
def report_miss_checkin():
    """
    上报漏打卡（Controller）
    """
    current_app.logger.info('=== 开始执行上报漏打卡接口 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    # 参数验证
    openid = decoded.get('openid')
    user = UserService.query_user_by_openid(openid)
    if not user:
        current_app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    # 获取请求参数
    params = request.get_json()
    if not params:
        current_app.logger.warning('上报漏打卡请求缺少请求体参数')
        return make_err_response({}, '缺少请求参数')

    rule_id = params.get('rule_id')
    miss_date_str = params.get('miss_date')
    reason = params.get('reason', '')

    if not rule_id:
        current_app.logger.warning('上报漏打卡请求缺少rule_id参数')
        return make_err_response({}, '缺少规则ID参数')

    if not miss_date_str:
        current_app.logger.warning('上报漏打卡请求缺少miss_date参数')
        return make_err_response({}, '缺少漏打卡日期参数')

    try:
        # 解析漏打卡日期
        miss_date = parse_date_only(miss_date_str)
        if not miss_date:
            current_app.logger.error(f'漏打卡日期格式错误: {miss_date_str}')
            return make_err_response({}, '漏打卡日期格式错误')

        # 调用 Service 层上报漏打卡
        response_data = CheckinRecordService.report_miss_checkin(
            user.user_id, rule_id, miss_date, reason
        )

        current_app.logger.info(
            f'用户 {user.user_id} 成功上报漏打卡，规则ID: {rule_id}, 漏打卡日期: {miss_date_str}')
        return make_succ_response(response_data)

    except Exception as e:
        current_app.logger.error(f'上报漏打卡时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'上报漏打卡失败: {str(e)}')


@checkin_bp.route('/checkin/cancel', methods=['POST'])
def cancel_checkin():
    """
    取消打卡（Controller）
    """
    current_app.logger.info('=== 开始执行取消打卡接口 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    # 参数验证
    openid = decoded.get('openid')
    user = UserService.query_user_by_openid(openid)
    if not user:
        current_app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    # 获取请求参数
    params = request.get_json()
    if not params:
        current_app.logger.warning('取消打卡请求缺少请求体参数')
        return make_err_response({}, '缺少请求参数')

    record_id = params.get('record_id')
    reason = params.get('reason', '')

    if not record_id:
        current_app.logger.warning('取消打卡请求缺少record_id参数')
        return make_err_response({}, '缺少记录ID参数')

    try:
        # 调用 Service 层取消打卡
        response_data = CheckinRecordService.cancel_checkin(
            user.user_id, record_id, reason
        )

        current_app.logger.info(
            f'用户 {user.user_id} 成功取消打卡，记录ID: {record_id}')
        return make_succ_response(response_data)

    except Exception as e:
        current_app.logger.error(f'取消打卡时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'取消打卡失败: {str(e)}')


@checkin_bp.route('/checkin/history', methods=['GET'])
def get_checkin_history():
    """
    获取打卡历史记录（Controller）
    """
    current_app.logger.info('=== 开始执行获取打卡历史记录接口 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    # 参数验证
    openid = decoded.get('openid')
    user = UserService.query_user_by_openid(openid)
    if not user:
        current_app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    # 获取查询参数
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 20)), 100)

    try:
        # 解析日期参数
        start_date = None
        end_date = None
        
        if start_date_str:
            start_date = parse_date_only(start_date_str)
            if not start_date:
                current_app.logger.error(f'开始日期格式错误: {start_date_str}')
                return make_err_response({}, '开始日期格式错误')
        
        if end_date_str:
            end_date = parse_date_only(end_date_str)
            if not end_date:
                current_app.logger.error(f'结束日期格式错误: {end_date_str}')
                return make_err_response({}, '结束日期格式错误')

        # 调用 Service 层获取打卡历史
        response_data = CheckinRecordService.get_checkin_history(
            user.user_id, start_date, end_date, page, per_page
        )

        current_app.logger.info(
            f'用户 {user.user_id} 成功获取打卡历史记录，记录数: {response_data["total"]}')
        return make_succ_response(response_data)

    except Exception as e:
        current_app.logger.error(f'获取打卡历史记录时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取打卡历史记录失败: {str(e)}')


@checkin_bp.route('/checkin/rules', methods=['GET', 'POST', 'PUT', 'DELETE'])
def manage_checkin_rules():
    """
    打卡规则管理接口（Controller）
    支持多种HTTP方法：GET（查询）、POST（创建）、PUT（更新）、DELETE（删除）
    """
    current_app.logger.info('=== 开始执行打卡规则管理接口 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    # 参数验证
    openid = decoded.get('openid')
    user = UserService.query_user_by_openid(openid)
    if not user:
        current_app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    method = request.method
    current_app.logger.info(f'打卡规则管理请求方法: {method}')

    try:
        if method == 'GET':
            # 查询打卡规则
            rule_id = request.args.get('rule_id')
            if rule_id:
                # 查询单个规则
                rule = CheckinRuleService.query_rule_by_id(int(rule_id))
                if not rule:
                    return make_err_response({}, '规则不存在')
                response_data = _rule_to_dict(rule)
            else:
                # 查询所有规则
                rules = CheckinRuleService.query_rules_by_user_id(user.user_id)
                response_data = {'rules': [_rule_to_dict(r) for r in rules]}

            current_app.logger.info(f'用户 {user.user_id} 成功查询打卡规则')
            return make_succ_response(response_data)

        elif method == 'POST':
            # 创建打卡规则
            params = request.get_json()
            if not params:
                return make_err_response({}, '缺少请求参数')

            # 支持新旧两种参数格式
            # 新格式：rule_name, frequency_type, time_slot_type, week_days, custom_time
            # 旧格式：title, checkin_time, repeat_days（向后兼容）
            if 'rule_name' in params:
                # 新格式验证
                if not params.get('rule_name'):
                    return make_err_response({}, '规则名称不能为空')
            else:
                # 旧格式验证（向后兼容）
                required_fields = ['title', 'checkin_time', 'repeat_days']
                for field in required_fields:
                    if field not in params:
                        return make_err_response({}, f'缺少必要参数: {field}')

            rule = CheckinRuleService.create_rule(params, user.user_id)
            current_app.logger.info(f'用户 {user.user_id} 成功创建打卡规则')
            return make_succ_response({'rule': _rule_to_dict(rule)})

        elif method == 'PUT':
            # 更新打卡规则
            params = request.get_json()
            if not params:
                return make_err_response({}, '缺少请求参数')

            # 支持新旧两种参数格式
            # 新格式：rule_id 作为路径参数或body参数
            rule_id = params.get('rule_id')
            if not rule_id:
                return make_err_response({}, '缺少规则ID参数')

            rule = CheckinRuleService.update_rule(rule_id, params, user.user_id)
            current_app.logger.info(f'用户 {user.user_id} 成功更新打卡规则')
            return make_succ_response({'rule': _rule_to_dict(rule)})

        elif method == 'DELETE':
            # 删除打卡规则
            rule_id = request.args.get('rule_id')
            if not rule_id:
                return make_err_response({}, '缺少规则ID参数')

            response_data = CheckinRuleService.delete_rule(int(rule_id), user.user_id)
            current_app.logger.info(f'用户 {user.user_id} 成功删除打卡规则')
            return make_succ_response(response_data)

        else:
            return make_err_response({}, '不支持的请求方法')

    except Exception as e:
        current_app.logger.error(f'打卡规则管理时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'打卡规则管理失败: {str(e)}')