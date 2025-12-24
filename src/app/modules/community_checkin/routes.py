"""
社区打卡规则视图模块
处理社区打卡规则相关的HTTP请求
"""
import logging
from functools import wraps
from flask import request, current_app
from . import community_checkin_bp
from app.shared import make_succ_response, make_err_response
from app.shared.decorators import login_required
from app.shared.utils.auth import verify_token
from wxcloudrun.community_checkin_rule_service import CommunityCheckinRuleService
from wxcloudrun.community_service import CommunityService
from database.flask_models import CommunityCheckinRule, db

logger = logging.getLogger('CommunityCheckinView')


def community_permission_required(f):
    """检查用户是否有社区管理权限的装饰器"""
    @wraps(f)
    def decorated_function(decoded, *args, **kwargs):
        # Layer 4: 调试仪表 - 记录权限检查开始
        logger.debug(f"=== Layer 4: 调试仪表 - 开始社区权限检查 ===")
        logger.debug(f"请求路径: {request.path}")
        logger.debug(f"请求方法: {request.method}")
        logger.debug(f"解码的用户信息: {decoded}")
        
        user_id = decoded.get('user_id')
        if not user_id:
            logger.warning("用户信息无效: decoded中没有user_id")
            return make_err_response({}, '用户信息无效')

        community_id = None

        # 1. 首先从查询参数获取community_id
        community_id = request.args.get('community_id')
        logger.debug(f"从查询参数获取community_id: {community_id}")

        # 2. 如果没有从查询参数获取到，尝试从JSON请求体获取（优雅处理空请求体）
        if not community_id:
            try:
                json_data = request.get_json(silent=True)
                logger.debug(f"请求体JSON数据: {json_data}")
                if json_data:
                    community_id = json_data.get('community_id')
                    logger.debug(f"从请求体JSON获取community_id: {community_id}")
            except Exception as e:
                logger.debug(f"JSON解析失败: {str(e)}")
                # 如果JSON解析失败，忽略错误

        # 3. 从路径参数获取（对于PUT/DELETE等操作）
        if not community_id and 'rule_id' in kwargs:
            rule_id = kwargs.get('rule_id')
            if rule_id:
                try:
                    rule = CommunityCheckinRule.query.get(rule_id)
                    if rule:
                        community_id = rule.community_id
                        logger.debug(f"从规则ID获取community_id: {community_id}")
                except Exception as e:
                    logger.debug(f"从规则ID获取community_id失败: {str(e)}")

        if not community_id:
            logger.warning("无法获取community_id")
            return make_err_response({}, '缺少社区ID参数')

        # 4. 验证用户权限
        logger.debug(f"开始验证用户 {user_id} 对社区 {community_id} 的权限")
        has_permission = CommunityService.has_community_permission(user_id, community_id)
        logger.debug(f"权限验证结果: {has_permission}")

        if not has_permission:
            logger.warning(f"用户 {user_id} 无权限管理社区 {community_id}")
            return make_err_response({}, '无权限管理该社区')

        # 5. 将社区信息存储到请求上下文
        g.user_id = user_id
        g.community_id = community_id
        logger.debug(f"权限验证通过，用户 {user_id} 有权限管理社区 {community_id}")

        return f(decoded, *args, **kwargs)
    return decorated_function


@community_checkin_bp.route('/rules', methods=['GET'])
@login_required
@community_permission_required
def get_community_checkin_rules(decoded):
    """
    获取社区打卡规则列表
    """
    current_app.logger.info('=== 开始获取社区打卡规则列表 ===')
    
    user_id = decoded.get('user_id')
    community_id = g.community_id
    
    try:
        # 获取查询参数
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        status_filter = request.args.get('status')  # 可选的状态过滤

        # 调用服务层获取规则列表
        result = CommunityCheckinRuleService.get_community_rules(
            community_id, page, per_page, status_filter
        )

        current_app.logger.info(f'成功获取社区 {community_id} 的打卡规则列表，共 {len(result.get("rules", []))} 条规则')
        return make_succ_response(result)

    except Exception as e:
        current_app.logger.error(f'获取社区打卡规则列表失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取规则列表失败: {str(e)}')


@community_checkin_bp.route('/rules', methods=['POST'])
@login_required
@community_permission_required
def create_community_checkin_rule(decoded):
    """
    创建社区打卡规则
    """
    current_app.logger.info('=== 开始创建社区打卡规则 ===')
    
    user_id = decoded.get('user_id')
    community_id = g.community_id
    
    try:
        # 获取请求参数
        params = request.get_json()
        if not params:
            return make_err_response({}, '缺少请求参数')

        # 验证必要参数
        required_fields = ['title', 'checkin_time', 'repeat_days']
        for field in required_fields:
            if field not in params:
                return make_err_response({}, f'缺少必要参数: {field}')

        # 调用服务层创建规则
        rule = CommunityCheckinRuleService.create_rule(
            community_id, user_id, params
        )

        current_app.logger.info(f'成功创建社区打卡规则，规则ID: {rule.rule_id}')
        return make_succ_response({
            'rule_id': rule.rule_id,
            'message': '创建成功'
        })

    except Exception as e:
        current_app.logger.error(f'创建社区打卡规则失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'创建规则失败: {str(e)}')


@community_checkin_bp.route('/rules/<int:rule_id>', methods=['PUT'])
@login_required
@community_permission_required
def update_community_checkin_rule(decoded, rule_id):
    """
    更新社区打卡规则
    """
    current_app.logger.info(f'=== 开始更新社区打卡规则: {rule_id} ===')
    
    user_id = decoded.get('user_id')
    community_id = g.community_id
    
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


@community_checkin_bp.route('/rules/<int:rule_id>/enable', methods=['POST'])
@login_required
@community_permission_required
def enable_community_checkin_rule(decoded, rule_id):
    """
    启用社区打卡规则
    """
    current_app.logger.info(f'=== 开始启用社区打卡规则: {rule_id} ===')
    
    user_id = decoded.get('user_id')
    community_id = g.community_id
    
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


@community_checkin_bp.route('/rules/<int:rule_id>/disable', methods=['POST'])
@login_required
@community_permission_required
def disable_community_checkin_rule(decoded, rule_id):
    """
    禁用社区打卡规则
    """
    current_app.logger.info(f'=== 开始禁用社区打卡规则: {rule_id} ===')
    
    user_id = decoded.get('user_id')
    community_id = g.community_id
    
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


@community_checkin_bp.route('/rules/<int:rule_id>', methods=['DELETE'])
@login_required
@community_permission_required
def delete_community_checkin_rule(decoded, rule_id):
    """
    删除社区打卡规则
    """
    current_app.logger.info(f'=== 开始删除社区打卡规则: {rule_id} ===')
    
    user_id = decoded.get('user_id')
    community_id = g.community_id
    
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


@community_checkin_bp.route('/rules/<int:rule_id>', methods=['GET'])
@login_required
@community_permission_required
def get_community_checkin_rule(decoded, rule_id):
    """
    获取单个社区打卡规则详情
    """
    current_app.logger.info(f'=== 开始获取社区打卡规则详情: {rule_id} ===')
    
    user_id = decoded.get('user_id')
    community_id = g.community_id
    
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