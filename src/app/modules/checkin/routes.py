"""
打卡功能模块路由
负责参数验证、调用 UseCase 层、返回响应
"""

import logging
from datetime import datetime, date, timedelta
from flask import request, current_app
from . import checkin_bp
from app.shared import make_succ_response, make_err_response
from app.shared.decorators import login_required
from app.shared.utils.auth import verify_token
from app.shared.utils.route_helpers import with_user_verification, get_json_params, execute_use_case, handle_use_case_result
from wxcloudrun.utils.timeutil import parse_date_only, parse_time_only

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
@with_user_verification
def get_today_checkin_items(user_id: int, user: dict):
    """
    获取用户今日打卡事项列表（Controller）
    """
    current_app.logger.info('=== 开始执行获取今日打卡事项接口 ===')

    from app.application.use_cases.checkin import GetTodayCheckinsUseCase

    try:
        result = execute_use_case(GetTodayCheckinsUseCase, user_id=user_id)

        if not result.is_success:
            return make_err_response({}, result.message)

        current_app.logger.info(
            f'成功获取今日打卡事项，用户ID: {user["user_id"]}, 事项数量: {len(result.data.get("checkin_items", []))}')
        return make_succ_response(result.data)

    except Exception as e:
        current_app.logger.error(f'获取今日打卡事项时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取今日打卡事项失败: {str(e)}')


@checkin_bp.route('/checkin', methods=['POST'])
@with_user_verification
def perform_checkin(user_id: int, user: dict):
    """
    执行打卡操作（Controller）
    """
    current_app.logger.info('=== 开始执行打卡操作接口 ===')

    # 获取并验证请求参数
    params, error_msg = get_json_params(required_fields=['rule_id'])
    if error_msg:
        current_app.logger.warning(f'打卡请求参数错误: {error_msg}')
        return make_err_response({}, error_msg)

    rule_id = params.get('rule_id')

    try:
        from app.application.use_cases.checkin import PerformCheckinUseCase

        result = execute_use_case(PerformCheckinUseCase, rule_id=rule_id, user_id=user_id)

        if not result.is_success:
            return make_err_response({}, result.message)

        current_app.logger.info(f'用户 {user["user_id"]} 成功打卡，规则ID: {rule_id}')
        return make_succ_response(result.data)

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
    user_id = decoded.get('user_id')
    from app.application.use_cases.user import GetUserByIdUseCase
    get_user_use_case = GetUserByIdUseCase()
    user_result = get_user_use_case.execute(user_id=user_id)
    if not user_result.is_success:
        current_app.logger.error(f'数据库中未找到user_id为 {user_id} 的用户')
        return make_err_response({}, '用户不存在')
    user = user_result.data

    # 获取请求参数
    params = request.get_json()
    if not params:
        current_app.logger.warning('上报漏打卡请求缺少请求体参数')
        return make_err_response({}, '缺少请求参数')

    rule_id = params.get('rule_id')

    if not rule_id:
        current_app.logger.warning('上报漏打卡请求缺少rule_id参数')
        return make_err_response({}, '缺少规则ID参数')

    try:
        # 使用应用服务用例上报漏打卡
        from app.application.use_cases.checkin import ReportMissCheckinUseCase

        use_case = ReportMissCheckinUseCase()
        result = use_case.execute(rule_id=rule_id, user_id=user_id)

        if not result.is_success:
            return make_err_response({}, result.message)

        current_app.logger.info(
            f'用户 {user['user_id']} 成功上报漏打卡，规则ID: {rule_id}')
        return make_succ_response(result.data)

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
    user_id = decoded.get('user_id')
    from app.application.use_cases.user import GetUserByIdUseCase
    get_user_use_case = GetUserByIdUseCase()
    user_result = get_user_use_case.execute(user_id=user_id)
    if not user_result.is_success:
        current_app.logger.error(f'数据库中未找到user_id为 {user_id} 的用户')
        return make_err_response({}, '用户不存在')
    user = user_result.data

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
        # 使用应用服务用例取消打卡
        from app.application.use_cases.checkin import CancelCheckinUseCase

        use_case = CancelCheckinUseCase()
        result = use_case.execute(record_id=record_id, user_id=user_id, reason=reason)

        if not result.is_success:
            return make_err_response({}, result.message)

        current_app.logger.info(
            f'用户 {user['user_id']} 成功取消打卡，记录ID: {record_id}')
        return make_succ_response(result.data)

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
    user_id = decoded.get('user_id')
    from app.application.use_cases.user import GetUserByIdUseCase
    get_user_use_case = GetUserByIdUseCase()
    user_result = get_user_use_case.execute(user_id=user_id)
    if not user_result.is_success:
        current_app.logger.error(f'数据库中未找到user_id为 {user_id} 的用户')
        return make_err_response({}, '用户不存在')
    user = user_result.data

    # 获取查询参数
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 20)), 100)

    try:
        # 解析日期参数
        from wxcloudrun.utils.timeutil import parse_date_only

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

        # 使用应用服务用例获取打卡历史
        from app.application.use_cases.checkin import GetCheckinHistoryUseCase

        use_case = GetCheckinHistoryUseCase()
        result = use_case.execute(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=per_page
        )

        if not result.is_success:
            return make_err_response({}, result.message)

        current_app.logger.info(
            f'用户 {user['user_id']} 成功获取打卡历史记录，记录数: {result.data.get("total", 0)}')
        return make_succ_response(result.data)

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
    user_id = decoded.get('user_id')
    from app.application.use_cases.user import GetUserByIdUseCase
    get_user_use_case = GetUserByIdUseCase()
    user_result = get_user_use_case.execute(user_id=user_id)
    if not user_result.is_success:
        current_app.logger.error(f'数据库中未找到user_id为 {user_id} 的用户')
        return make_err_response({}, '用户不存在')
    user = user_result.data  # user 现在是一个字典

    method = request.method
    current_app.logger.info(f'打卡规则管理请求方法: {method}')

    try:
        if method == 'GET':
            # 查询打卡规则
            rule_id = request.args.get('rule_id')

            # 使用应用服务用例查询打卡规则
            from app.application.use_cases.checkin import GetCheckinRuleUseCase

            use_case = GetCheckinRuleUseCase()
            result = use_case.execute(user_id=user['user_id'], rule_id=int(rule_id) if rule_id else None)

            if not result.is_success:
                return make_err_response({}, result.message)

            # 构造响应数据
            if rule_id:
                # 单个规则
                rule = result.data.get('rule')
                response_data = _rule_to_dict(rule)
            else:
                # 所有规则
                rules = result.data.get('rules', [])
                response_data = {'rules': [_rule_to_dict(r) for r in rules]}

            current_app.logger.info(f'用户 {user['user_id']} 成功查询打卡规则')
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

            # 使用应用服务用例创建打卡规则
            from app.application.use_cases.checkin import CreateCheckinRuleUseCase

            use_case = CreateCheckinRuleUseCase()
            result = use_case.execute(user_id=user_id, rule_data=params)

            if not result.is_success:
                return make_err_response({}, result.message)

            rule = result.data.get('rule')
            current_app.logger.info(f'用户 {user['user_id']} 成功创建打卡规则')
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

            # 使用应用服务用例更新打卡规则
            from app.application.use_cases.checkin import UpdateCheckinRuleUseCase

            use_case = UpdateCheckinRuleUseCase()
            result = use_case.execute(rule_id=rule_id, user_id=user_id, rule_data=params)

            if not result.is_success:
                return make_err_response({}, result.message)

            rule = result.data.get('rule')
            current_app.logger.info(f'用户 {user['user_id']} 成功更新打卡规则')
            return make_succ_response({'rule': _rule_to_dict(rule)})

        elif method == 'DELETE':
            # 删除打卡规则
            rule_id = request.args.get('rule_id')
            if not rule_id:
                return make_err_response({}, '缺少规则ID参数')

            # 使用应用服务用例删除打卡规则
            from app.application.use_cases.checkin import DeleteCheckinRuleUseCase

            use_case = DeleteCheckinRuleUseCase()
            result = use_case.execute(rule_id=int(rule_id), user_id=user_id)

            if not result.is_success:
                return make_err_response({}, result.message)

            current_app.logger.info(f'用户 {user['user_id']} 成功删除打卡规则')
            return make_succ_response({'message': '规则删除成功'})

        else:
            return make_err_response({}, '不支持的请求方法')

    except Exception as e:
        current_app.logger.error(f'打卡规则管理时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'打卡规则管理失败: {str(e)}')