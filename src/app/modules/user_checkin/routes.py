"""
用户打卡规则视图模块
处理用户规则查询和聚合的HTTP请求（个人规则 + 社区规则）
"""
import logging
from flask import request, current_app
from . import user_checkin_bp
from app.shared import make_succ_response, make_err_response
from app.shared.decorators import login_required
from app.shared.utils.auth import verify_token
from wxcloudrun.user_checkin_rule_service import UserCheckinRuleService

logger = logging.getLogger('UserCheckinView')


@user_checkin_bp.route('/user-checkin/rules', methods=['GET', 'DELETE'])
def get_user_all_rules():
    """
    获取用户所有打卡规则（个人规则 + 社区规则）
    GET /api/user-checkin/rules

    Response:
    {
        "code": 1,
        "msg": "success",
        "data": [
            {
                // 社区规则（优先显示）
                "community_rule_id": 1,
                "rule_name": "社区健康打卡",
                "icon_url": "...",
                "frequency_type": 0,
                "time_slot_type": 4,
                "custom_time": "09:00:00",
                "rule_source": "community",
                "is_editable": false,
                "source_label": "社区规则",
                "community_name": "安卡大家庭",
                "created_by_name": "张主管",
                "is_enabled": true
            },
            {
                // 个人规则（在社区规则后显示）
                "rule_id": 1,
                "rule_name": "个人每日阅读",
                "icon_url": "...",
                "frequency_type": 0,
                "time_slot_type": 4,
                "custom_time": "20:00:00",
                "rule_source": "personal",
                "is_editable": true,
                "source_label": "个人规则",
                "is_enabled": true
            }
        ]
    }
    """
    current_app.logger.info('=== 开始获取用户所有打卡规则 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    current_app.logger.info(f'用户ID: {user_id}')

    # 处理 DELETE 方法（删除个人规则）
    if request.method == 'DELETE':
        params = request.get_json()
        if not params:
            return make_err_response({}, '缺少请求参数')

        rule_id = params.get('rule_id')
        rule_source = params.get('rule_source')

        if not rule_id:
            return make_err_response({}, '缺少规则ID参数')

        # 只允许删除个人规则
        if rule_source == 'community':
            return make_err_response({}, '不允许删除社区规则')

        try:
            # 调用 CheckinRuleService 删除个人规则
            from wxcloudrun.checkin_rule_service import CheckinRuleService
            response_data = CheckinRuleService.delete_rule(int(rule_id), user_id)
            current_app.logger.info(f'用户 {user_id} 成功删除个人打卡规则')
            return make_succ_response(response_data)
        except Exception as e:
            current_app.logger.error(f'删除个人打卡规则失败: {str(e)}', exc_info=True)
            return make_err_response({}, f'删除规则失败: {str(e)}')

    # 处理 GET 方法（获取所有规则）
    try:
        # 调用服务层获取用户所有规则
        rules = UserCheckinRuleService.get_user_all_rules(user_id)

        current_app.logger.info(f'成功获取用户 {user_id} 的所有打卡规则，共 {len(rules)} 条规则')
        return make_succ_response(rules)

    except Exception as e:
        current_app.logger.error(f'获取用户所有打卡规则失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取规则失败: {str(e)}')


@user_checkin_bp.route('/user-checkin/today-plan', methods=['GET'])
def get_user_today_plan():
    """
    获取用户今日打卡计划
    GET /api/user-checkin/today-plan

    Response:
    {
        "code": 1,
        "msg": "success",
        "data": {
            "date": "2025-12-24",
            "total_items": 3,
            "completed_items": 1,
            "pending_items": 2,
            "items": [
                {
                    "item_id": 1,
                    "rule_id": 1,
                    "community_rule_id": null,
                    "rule_name": "社区健康打卡",
                    "icon_url": "...",
                    "checkin_time": "09:00:00",
                    "is_completed": true,
                    "completed_at": "2025-12-24 08:45:00",
                    "rule_source": "community",
                    "source_label": "社区规则",
                    "community_name": "安卡大家庭"
                }
            ]
        }
    }
    """
    current_app.logger.info('=== 开始获取用户今日打卡计划 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    current_app.logger.info(f'用户ID: {user_id}')

    try:
        # 调用服务层获取今日打卡计划
        plan = UserCheckinRuleService.get_today_checkin_plan(user_id)

        current_app.logger.info(f'成功获取用户 {user_id} 的今日打卡计划，共 {plan.get("total_items", 0)} 项')
        return make_succ_response(plan)

    except Exception as e:
        current_app.logger.error(f'获取用户今日打卡计划失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取今日计划失败: {str(e)}')


@user_checkin_bp.route('/user-checkin/rules/<int:rule_id>', methods=['GET'])
def get_user_rule_detail(rule_id):
    """
    获取用户打卡规则详情
    GET /api/user-checkin/rules/{rule_id}

    Response:
    {
        "code": 1,
        "msg": "success",
        "data": {
            "rule_id": 1,
            "rule_name": "社区健康打卡",
            "icon_url": "...",
            "frequency_type": 0,
            "time_slot_type": 4,
            "custom_time": "09:00:00",
            "rule_source": "community",
            "is_editable": false,
            "source_label": "社区规则",
            "community_name": "安卡大家庭",
            "created_by_name": "张主管",
            "is_enabled": true,
            "created_at": "2025-12-20 10:00:00",
            "updated_at": "2025-12-22 15:30:00"
        }
    }
    """
    current_app.logger.info(f'=== 开始获取用户打卡规则详情: {rule_id} ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    current_app.logger.info(f'用户ID: {user_id}, 规则ID: {rule_id}')

    try:
        # 调用服务层获取规则详情
        rule = UserCheckinRuleService.get_user_rule_detail(user_id, rule_id)

        current_app.logger.info(f'成功获取用户 {user_id} 的规则详情，规则ID: {rule_id}')
        return make_succ_response(rule)

    except Exception as e:
        current_app.logger.error(f'获取用户打卡规则详情失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取规则详情失败: {str(e)}')


@user_checkin_bp.route('/user-checkin/statistics', methods=['GET'])
def get_user_checkin_statistics():
    """
    获取用户打卡统计信息
    GET /api/user-checkin/statistics?period=week&start_date=2025-12-18&end_date=2025-12-24

    Response:
    {
        "code": 1,
        "msg": "success",
        "data": {
            "period": "week",
            "total_days": 7,
            "checkin_days": 5,
            "checkin_rate": 71.4,
            "total_rules": 3,
            "completed_checkins": 15,
            "missed_checkins": 6,
            "daily_stats": [
                {
                    "date": "2025-12-18",
                    "total_rules": 3,
                    "completed_rules": 2,
                    "missed_rules": 1,
                    "checkin_rate": 66.7
                }
            ]
        }
    }
    """
    current_app.logger.info('=== 开始获取用户打卡统计信息 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    current_app.logger.info(f'用户ID: {user_id}')

    try:
        # 获取查询参数
        period = request.args.get('period', 'week')  # week, month
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # 调用服务层获取统计信息
        stats = UserCheckinRuleService.get_user_checkin_statistics(
            user_id, period, start_date, end_date
        )

        current_app.logger.info(f'成功获取用户 {user_id} 的打卡统计信息')
        return make_succ_response(stats)

    except Exception as e:
        current_app.logger.error(f'获取用户打卡统计信息失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取统计信息失败: {str(e)}')


@user_checkin_bp.route('/user-checkin/rules/source-info', methods=['POST'])
def get_rules_source_info():
    """
    批量获取规则来源信息
    POST /api/user-checkin/rules/source-info

    Request:
    {
        "rule_ids": [1, 2, 3],
        "community_rule_ids": [1, 2]
    }

    Response:
    {
        "code": 1,
        "msg": "success",
        "data": {
            "personal_rules": [
                {
                    "rule_id": 1,
                    "rule_name": "个人阅读",
                    "is_enabled": true
                }
            ],
            "community_rules": [
                {
                    "community_rule_id": 1,
                    "rule_name": "社区健康打卡",
                    "community_name": "安卡大家庭",
                    "is_enabled": true
                }
            ]
        }
    }
    """
    current_app.logger.info('=== 开始批量获取规则来源信息 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    current_app.logger.info(f'用户ID: {user_id}')

    try:
        # 获取请求参数
        params = request.get_json()
        if not params:
            return make_err_response({}, '缺少请求参数')

        rule_ids = params.get('rule_ids', [])
        community_rule_ids = params.get('community_rule_ids', [])

        # 调用服务层获取规则来源信息
        source_info = UserCheckinRuleService.get_rules_source_info(
            user_id, rule_ids, community_rule_ids
        )

        current_app.logger.info(f'成功获取用户 {user_id} 的规则来源信息')
        return make_succ_response(source_info)

    except Exception as e:
        current_app.logger.error(f'批量获取规则来源信息失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取来源信息失败: {str(e)}')