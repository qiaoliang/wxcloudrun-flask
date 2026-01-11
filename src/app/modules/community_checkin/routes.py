"""
社区打卡规则视图模块
处理社区打卡规则相关的HTTP请求
"""
import logging
from functools import wraps
from flask import request, current_app
from . import community_checkin_bp
from app.shared import make_succ_response, make_err_response
from app.shared.decorators import login_required, require_community_staff_member
from app.shared.utils.auth import verify_token
from database.flask_models import CommunityCheckinRule, db
from app.application.use_cases.community_checkin import (
    GetCommunityCheckinRulesUseCase,
    CreateCommunityCheckinRuleUseCase,
    UpdateCommunityCheckinRuleUseCase,
    EnableCommunityCheckinRuleUseCase,
    DisableCommunityCheckinRuleUseCase,
    DeleteCommunityCheckinRuleUseCase,
    GetCommunityCheckinRuleUseCase,
    GetCommunityDailyStatsUseCase,
    GetCommunityCheckinStatsUseCase
)

logger = logging.getLogger('CommunityCheckinView')





@community_checkin_bp.route('/rules', methods=['GET'])
@require_community_staff_member()
def get_community_checkin_rules(decoded):
    """
    获取社区打卡规则列表
    """
    current_app.logger.info('=== 开始获取社区打卡规则列表 ===')

    user_id = decoded.get('user_id')
    # 从请求参数获取 community_id
    community_id = request.args.get('community_id')
    if not community_id:
        return make_err_response({}, '缺少社区ID参数')
    community_id = int(community_id)

    try:
        # 获取查询参数
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        status_filter = request.args.get('status')  # 可选的状态过滤
        grouped = request.args.get('grouped', 'false').lower() == 'true'  # 是否返回分组数据

        use_case = GetCommunityCheckinRulesUseCase()
        result = use_case.execute(community_id, page, per_page, status_filter, grouped)

        if result['success']:
            return make_succ_response(result['data'])
        else:
            return make_err_response(result['data'], result['message'])

    except Exception as e:
        current_app.logger.error(f'获取社区打卡规则列表失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取规则列表失败: {str(e)}')


@community_checkin_bp.route('/rules', methods=['POST'])
@require_community_staff_member()
def create_community_checkin_rule(decoded):
    """
    创建社区打卡规则
    """
    current_app.logger.info('=== 开始创建社区打卡规则 ===')

    user_id = decoded.get('user_id')
    # 从请求体获取 community_id
    community_id = request.json.get('community_id')
    if not community_id:
        return make_err_response({}, '缺少社区ID参数')
    community_id = int(community_id)

    try:
        # 获取请求参数
        params = request.get_json()
        if not params:
            return make_err_response({}, '缺少请求参数')

        use_case = CreateCommunityCheckinRuleUseCase()
        result = use_case.execute(params, community_id, user_id)

        if result['success']:
            return make_succ_response(result['data'])
        else:
            return make_err_response(result['data'], result['message'])

    except Exception as e:
        current_app.logger.error(f'创建社区打卡规则失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'创建规则失败: {str(e)}')


@community_checkin_bp.route('/rules/<int:rule_id>', methods=['PUT'])
@require_community_staff_member()
def update_community_checkin_rule(decoded, rule_id):
    """
    更新社区打卡规则
    """
    current_app.logger.info(f'=== 开始更新社区打卡规则: {rule_id} ===')

    user_id = decoded.get('user_id')
    # 从规则ID获取 community_id
    rule = db.session.get(CommunityCheckinRule, rule_id)
    if not rule:
        return make_err_response({}, '规则不存在')
    community_id = rule.community_id

    try:
        # 获取请求参数
        params = request.get_json()
        if not params:
            return make_err_response({}, '缺少请求参数')

        use_case = UpdateCommunityCheckinRuleUseCase()
        result = use_case.execute(rule_id, params, user_id)

        if result['success']:
            return make_succ_response(result['data'])
        else:
            return make_err_response(result['data'], result['message'])

    except Exception as e:
        current_app.logger.error(f'更新社区打卡规则失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'更新规则失败: {str(e)}')


@community_checkin_bp.route('/rules/<int:rule_id>/enable', methods=['POST'])
@require_community_staff_member()
def enable_community_checkin_rule(decoded, rule_id):
    """
    启用社区打卡规则
    """
    current_app.logger.info(f'=== 开始启用社区打卡规则: {rule_id} ===')

    user_id = decoded.get('user_id')
    # 从规则ID获取 community_id
    rule = db.session.get(CommunityCheckinRule, rule_id)
    if not rule:
        return make_err_response({}, '规则不存在')
    community_id = rule.community_id

    try:
        use_case = EnableCommunityCheckinRuleUseCase()
        result = use_case.execute(rule_id, user_id)

        if result['success']:
            return make_succ_response(result['data'])
        else:
            return make_err_response(result['data'], result['message'])

    except Exception as e:
        current_app.logger.error(f'启用社区打卡规则失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'启用规则失败: {str(e)}')


@community_checkin_bp.route('/rules/<int:rule_id>/disable', methods=['POST'])
@require_community_staff_member()
def disable_community_checkin_rule(decoded, rule_id):
    """
    禁用社区打卡规则
    """
    current_app.logger.info(f'=== 开始禁用社区打卡规则: {rule_id} ===')

    user_id = decoded.get('user_id')
    # 从规则ID获取 community_id
    rule = db.session.get(CommunityCheckinRule, rule_id)
    if not rule:
        return make_err_response({}, '规则不存在')
    community_id = rule.community_id

    try:
        use_case = DisableCommunityCheckinRuleUseCase()
        result = use_case.execute(rule_id, user_id)

        if result['success']:
            return make_succ_response(result['data'])
        else:
            return make_err_response(result['data'], result['message'])

    except Exception as e:
        current_app.logger.error(f'禁用社区打卡规则失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'禁用规则失败: {str(e)}')


@community_checkin_bp.route('/rules/<int:rule_id>', methods=['DELETE'])
@require_community_staff_member()
def delete_community_checkin_rule(decoded, rule_id):
    """
    删除社区打卡规则
    """
    current_app.logger.info(f'=== 开始删除社区打卡规则: {rule_id} ===')

    user_id = decoded.get('user_id')
    # 从规则ID获取 community_id
    rule = db.session.get(CommunityCheckinRule, rule_id)
    if not rule:
        return make_err_response({}, '规则不存在')
    community_id = rule.community_id

    try:
        use_case = DeleteCommunityCheckinRuleUseCase()
        result = use_case.execute(rule_id, user_id)

        if result['success']:
            return make_succ_response(result['data'])
        else:
            return make_err_response(result['data'], result['message'])

    except Exception as e:
        current_app.logger.error(f'删除社区打卡规则失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'删除规则失败: {str(e)}')


@community_checkin_bp.route('/rules/<int:rule_id>', methods=['GET'])
@require_community_staff_member()
def get_community_checkin_rule(decoded, rule_id):
    """
    获取单个社区打卡规则详情
    """
    current_app.logger.info(f'=== 开始获取社区打卡规则详情: {rule_id} ===')

    user_id = decoded.get('user_id')
    # 从规则ID获取 community_id
    rule = db.session.get(CommunityCheckinRule, rule_id)
    if not rule:
        return make_err_response({}, '规则不存在')
    community_id = rule.community_id

    try:
        use_case = GetCommunityCheckinRuleUseCase()
        result = use_case.execute(rule_id)

        if result['success']:
            return make_succ_response(result['data'])
        else:
            return make_err_response(result['data'], result['message'])

    except Exception as e:
        current_app.logger.error(f'获取社区打卡规则详情失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取规则详情失败: {str(e)}')


@community_checkin_bp.route('/stats/<int:community_id>/daily-stats', methods=['GET'])
@require_community_staff_member()
def get_community_daily_stats(decoded, community_id):
    """获取社区每日打卡统计"""
    current_app.logger.info(f'=== 开始获取社区每日统计: {community_id} ===')

    user_id = decoded.get('user_id')
    current_app.logger.info(f'用户ID: {user_id}')

    try:
        use_case = GetCommunityDailyStatsUseCase()
        result = use_case.execute(community_id, user_id)

        if result['success']:
            return make_succ_response(result['data'])
        else:
            return make_err_response(result['data'], result['message'])

    except Exception as e:
        current_app.logger.error(f'获取社区每日统计失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取统计信息失败: {str(e)}')


@community_checkin_bp.route('/stats/<int:community_id>/checkin-stats', methods=['GET'])
@require_community_staff_member()
def get_community_checkin_stats(decoded, community_id):
    """获取社区打卡统计信息"""
    current_app.logger.info(f'=== 开始获取社区打卡统计信息: {community_id} ===')

    user_id = decoded.get('user_id')
    current_app.logger.info(f'用户ID: {user_id}')

    try:
        # 获取查询参数
        days = request.args.get('days', 7, type=int)

        use_case = GetCommunityCheckinStatsUseCase()
        result = use_case.execute(community_id, user_id, days)

        if result['success']:
            return make_succ_response(result['data'])
        else:
            return make_err_response(result['data'], result['message'])

    except Exception as e:
        current_app.logger.error(f'获取社区打卡统计信息失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取统计信息失败: {str(e)}')