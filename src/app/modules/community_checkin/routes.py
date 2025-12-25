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
from wxcloudrun.community_checkin_rule_service import CommunityCheckinRuleService
from wxcloudrun.community_service import CommunityService
from database.flask_models import CommunityCheckinRule, db

logger = logging.getLogger('CommunityCheckinView')





@community_checkin_bp.route('/community_checkin/rules', methods=['GET'])
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

        # 调用服务层获取规则列表
        # TODO: 当前服务方法不支持分页，需要后续添加分页支持
        include_disabled = (status_filter == 'all')
        rules = CommunityCheckinRuleService.get_community_rules(
            community_id, include_disabled
        )
        
        # 简单包装结果格式，保持与预期一致
        result = {
            'rules': rules,
            'total': len(rules),
            'page': page,
            'per_page': per_page
        }

        current_app.logger.info(f'成功获取社区 {community_id} 的打卡规则列表，共 {len(result.get("rules", []))} 条规则')
        return make_succ_response(result)

    except Exception as e:
        current_app.logger.error(f'获取社区打卡规则列表失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取规则列表失败: {str(e)}')


@community_checkin_bp.route('/community_checkin/rules', methods=['POST'])
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

        # 验证必要参数
        required_fields = ['rule_name']
        for field in required_fields:
            if field not in params:
                return make_err_response({}, f'缺少必要参数: {field}')

        # 调用服务层创建规则
        rule = CommunityCheckinRuleService.create_community_rule(
            params, community_id, user_id
        )

        current_app.logger.info(f'成功创建社区打卡规则，规则ID: {rule.rule_id}')
        return make_succ_response({
            'rule_id': rule.rule_id,
            'message': '创建成功'
        })

    except Exception as e:
        current_app.logger.error(f'创建社区打卡规则失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'创建规则失败: {str(e)}')


@community_checkin_bp.route('/community_checkin/rules/<int:rule_id>', methods=['PUT'])
@require_community_staff_member()
def update_community_checkin_rule(decoded, rule_id):
    """
    更新社区打卡规则
    """
    current_app.logger.info(f'=== 开始更新社区打卡规则: {rule_id} ===')

    user_id = decoded.get('user_id')
    # 从规则ID获取 community_id
    rule = CommunityCheckinRule.query.get(rule_id)
    if not rule:
        return make_err_response({}, '规则不存在')
    community_id = rule.community_id

    try:
        # 获取请求参数
        params = request.get_json()
        if not params:
            return make_err_response({}, '缺少请求参数')

        # 调用服务层更新规则
        rule = CommunityCheckinRuleService.update_rule(
            rule_id, community_id, user_id, params
        )

        current_app.logger.info(f'成功更新社区打卡规则，规则ID: {rule.rule_id}')
        return make_succ_response({
            'rule_id': rule.rule_id,
            'message': '更新成功'
        })

    except Exception as e:
        current_app.logger.error(f'更新社区打卡规则失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'更新规则失败: {str(e)}')


@community_checkin_bp.route('/community_checkin/rules/<int:rule_id>/enable', methods=['POST'])
@require_community_staff_member()
def enable_community_checkin_rule(decoded, rule_id):
    """
    启用社区打卡规则
    """
    current_app.logger.info(f'=== 开始启用社区打卡规则: {rule_id} ===')

    user_id = decoded.get('user_id')
    # 从规则ID获取 community_id
    rule = CommunityCheckinRule.query.get(rule_id)
    if not rule:
        return make_err_response({}, '规则不存在')
    community_id = rule.community_id

    try:
        # 调用服务层启用规则
        rule = CommunityCheckinRuleService.enable_rule(
            rule_id, community_id, user_id
        )

        current_app.logger.info(f'成功启用社区打卡规则，规则ID: {rule.rule_id}')
        return make_succ_response({
            'rule_id': rule.rule_id,
            'message': '启用成功'
        })

    except Exception as e:
        current_app.logger.error(f'启用社区打卡规则失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'启用规则失败: {str(e)}')


@community_checkin_bp.route('/community_checkin/rules/<int:rule_id>/disable', methods=['POST'])
@require_community_staff_member()
def disable_community_checkin_rule(decoded, rule_id):
    """
    禁用社区打卡规则
    """
    current_app.logger.info(f'=== 开始禁用社区打卡规则: {rule_id} ===')

    user_id = decoded.get('user_id')
    # 从规则ID获取 community_id
    rule = CommunityCheckinRule.query.get(rule_id)
    if not rule:
        return make_err_response({}, '规则不存在')
    community_id = rule.community_id

    try:
        # 调用服务层禁用规则
        rule = CommunityCheckinRuleService.disable_rule(
            rule_id, community_id, user_id
        )

        current_app.logger.info(f'成功禁用社区打卡规则，规则ID: {rule.rule_id}')
        return make_succ_response({
            'rule_id': rule.rule_id,
            'message': '禁用成功'
        })

    except Exception as e:
        current_app.logger.error(f'禁用社区打卡规则失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'禁用规则失败: {str(e)}')


@community_checkin_bp.route('/community_checkin/rules/<int:rule_id>', methods=['DELETE'])
@require_community_staff_member()
def delete_community_checkin_rule(decoded, rule_id):
    """
    删除社区打卡规则
    """
    current_app.logger.info(f'=== 开始删除社区打卡规则: {rule_id} ===')

    user_id = decoded.get('user_id')
    # 从规则ID获取 community_id
    rule = CommunityCheckinRule.query.get(rule_id)
    if not rule:
        return make_err_response({}, '规则不存在')
    community_id = rule.community_id

    try:
        # 调用服务层删除规则
        success = CommunityCheckinRuleService.delete_rule(
            rule_id, community_id, user_id
        )

        if success:
            current_app.logger.info(f'成功删除社区打卡规则，规则ID: {rule_id}')
            return make_succ_response({
                'rule_id': rule_id,
                'message': '删除成功'
            })
        else:
            return make_err_response({}, '删除失败')

    except Exception as e:
        current_app.logger.error(f'删除社区打卡规则失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'删除规则失败: {str(e)}')


@community_checkin_bp.route('/community_checkin/rules/<int:rule_id>', methods=['GET'])
@require_community_staff_member()
def get_community_checkin_rule(decoded, rule_id):
    """
    获取单个社区打卡规则详情
    """
    current_app.logger.info(f'=== 开始获取社区打卡规则详情: {rule_id} ===')

    user_id = decoded.get('user_id')
    # 从规则ID获取 community_id
    rule = CommunityCheckinRule.query.get(rule_id)
    if not rule:
        return make_err_response({}, '规则不存在')
    community_id = rule.community_id

    try:
        # 调用服务层获取规则详情
        rule = CommunityCheckinRuleService.get_rule_by_id(
            rule_id, community_id, user_id
        )

        current_app.logger.info(f'成功获取社区打卡规则详情，规则ID: {rule.rule_id}')
        return make_succ_response(rule)

    except Exception as e:
        current_app.logger.error(f'获取社区打卡规则详情失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取规则详情失败: {str(e)}')