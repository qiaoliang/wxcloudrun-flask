"""
社区打卡规则视图模块
处理社区打卡规则相关的HTTP请求
"""
import logging
from flask import request, g
from wxcloudrun import app
from wxcloudrun.decorators import login_required
from wxcloudrun.community_checkin_rule_service import CommunityCheckinRuleService
from wxcloudrun.response import make_succ_response, make_err_response

logger = logging.getLogger('CommunityCheckinView')


def community_permission_required(f):
    """检查用户是否有社区管理权限的装饰器"""
    from functools import wraps
    from wxcloudrun.community_service import CommunityService
    from wxcloudrun.dao import get_db
    from database.models import CommunityCheckinRule

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

        # 3. 如果还没有community_id，尝试从表单数据获取
        if not community_id:
            community_id = request.form.get('community_id')
            logger.debug(f"从表单数据获取community_id: {community_id}")

        # 4. 如果还没有community_id，尝试从rule_id获取（对于启用/停用等端点）
        if not community_id and 'rule_id' in kwargs:
            try:
                rule_id = kwargs['rule_id']
                logger.debug(f"从kwargs获取rule_id: {rule_id}")
                # 直接查询数据库获取社区ID，避免复杂的对象加载
                with get_db().get_session() as session:
                    rule = session.query(CommunityCheckinRule).get(rule_id)
                    if rule:
                        community_id = rule.community_id
                        logger.debug(f"从数据库规则获取community_id: {community_id}")
                    else:
                        logger.warning(f"规则不存在: rule_id={rule_id}")
            except Exception as e:
                logger.warning(f"从规则ID获取社区ID失败: {str(e)}")
                # 继续执行，让下面的错误处理返回"缺少社区ID参数"

        if not community_id:
            logger.warning(f"缺少社区ID参数: user_id={user_id}, 所有来源都未找到")
            return make_err_response({}, '缺少社区ID参数')

        logger.debug(f"最终确定的community_id: {community_id}")

        # 检查用户是否是该社区的主管或专员
        has_permission = CommunityService.has_community_permission(user_id, community_id)
        logger.debug(f"权限检查结果: user_id={user_id}, community_id={community_id}, has_permission={has_permission}")
        
        if not has_permission:
            logger.warning(f"无社区管理权限: user_id={user_id}, community_id={community_id}")
            return make_err_response({}, '无社区管理权限')

        logger.debug(f"权限检查通过: user_id={user_id}, community_id={community_id}")
        return f(decoded, *args, **kwargs)
    return decorated_function


@app.route('/api/community-checkin/rules', methods=['GET'])
@login_required
@community_permission_required
def get_community_rules(decoded):
    """
    获取社区规则列表
    GET /api/community-checkin/rules?community_id=<community_id>&include_disabled=<true/false>

    Response:
    {
        "code": 1,
        "msg": "success",
        "data": {
            "rules": [
                {
                    "community_rule_id": 1,
                    "rule_name": "每日健康打卡",
                    "icon_url": "...",
                    "frequency_type": 0,
                    "time_slot_type": 4,
                    "custom_time": "09:00:00",
                    "is_enabled": false,
                    "status": 1,
                    "created_by": 123,
                    "updated_by": 123,
                    "created_at": "2025-12-19T10:00:00",
                    "updated_at": "2025-12-19T10:00:00",
                    "enabled_at": null,
                    "disabled_at": null,
                    "enabled_by": null,
                    "disabled_by": null
                }
            ]
        }
    }
    """
    try:
        # Layer 4: 调试仪表 - 记录请求详细信息
        logger.debug(f"=== Layer 4: 调试仪表 - 开始处理规则列表请求 ===")
        logger.debug(f"请求方法: {request.method}")
        logger.debug(f"请求URL: {request.url}")
        logger.debug(f"请求头: {dict(request.headers)}")
        logger.debug(f"查询参数: {dict(request.args)}")
        
        # 尝试从请求体获取数据（兼容前端错误实现）
        try:
            json_data = request.get_json(silent=True)
            if json_data:
                logger.debug(f"请求体JSON数据: {json_data}")
        except Exception as e:
            logger.debug(f"请求体解析失败: {str(e)}")
        
        # Layer 1: API入口点验证 - 支持多种参数来源
        community_id = None
        
        # 1. 优先从查询参数获取
        community_id = request.args.get('community_id')
        logger.debug(f"从查询参数获取community_id: {community_id}")
        
        # 2. 如果没有从查询参数获取到，尝试从JSON请求体获取（兼容前端错误）
        if not community_id:
            try:
                json_data = request.get_json(silent=True)
                if json_data:
                    community_id = json_data.get('community_id')
                    logger.debug(f"从请求体JSON获取community_id: {community_id}")
            except Exception as e:
                logger.debug(f"从请求体获取community_id失败: {str(e)}")
        
        # 3. 如果还没有，尝试从表单数据获取
        if not community_id:
            community_id = request.form.get('community_id')
            logger.debug(f"从表单数据获取community_id: {community_id}")
        
        # 获取include_disabled参数
        include_disabled = request.args.get('include_disabled', 'false').lower() == 'true'
        logger.debug(f"include_disabled参数: {include_disabled}")
        
        # 验证必要参数
        if not community_id:
            logger.warning("缺少社区ID参数，所有来源都未找到")
            return make_err_response({}, '缺少社区ID参数')

        try:
            community_id_int = int(community_id)
            if community_id_int <= 0:
                logger.warning(f"社区ID必须为正整数: {community_id_int}")
                return make_err_response({}, '社区ID必须为正整数')
        except ValueError:
            logger.warning(f"社区ID必须为有效整数: {community_id}")
            return make_err_response({}, '社区ID必须为有效整数')
        
        logger.debug(f"验证通过: community_id={community_id_int}, include_disabled={include_disabled}")

        rules_data = CommunityCheckinRuleService.get_community_rules(community_id_int, include_disabled)
        logger.info(f"获取社区规则列表成功: 社区ID={community_id_int}, 规则数量={len(rules_data)}")
        
        # Layer 4: 调试仪表 - 记录响应数据
        logger.debug(f"返回规则数据: {len(rules_data)}条规则")
        for i, rule in enumerate(rules_data[:3]):  # 只记录前3条规则
            logger.debug(f"规则{i+1}: id={rule.get('community_rule_id')}, name={rule.get('rule_name')}, status={rule.get('status')}")
        
        return make_succ_response({'rules': rules_data})

    except ValueError as e:
        logger.warning(f"获取社区规则列表参数错误: {str(e)}")
        return make_err_response({}, str(e))
    except Exception as e:
        logger.error(f"获取社区规则列表失败: {str(e)}")
        return make_err_response({}, f'获取社区规则列表失败: {str(e)}')


@app.route('/api/community-checkin/rules', methods=['POST'])
@login_required
@community_permission_required
def create_community_rule(decoded):
    """
    创建社区规则（默认未启用状态）
    POST /api/community-checkin/rules

    Request Body:
    {
        "community_id": 1,
        "rule_name": "每日健康打卡",
        "icon_url": "...",
        "frequency_type": 0,
        "time_slot_type": 4,
        "custom_time": "09:00:00",
        "custom_start_date": "2025-01-01",
        "custom_end_date": "2025-12-31",
        "week_days": 127
    }

    Response:
    {
        "code": 1,
        "msg": "创建社区规则成功",
        "data": {
            "community_rule_id": 1,
            "rule_name": "每日健康打卡",
            "is_enabled": false,
            "created_by": 123,
            "created_at": "2025-12-19T10:00:00"
        }
    }
    """
    try:
        data = request.get_json()
        community_id = data.get('community_id')
        created_by = decoded.get('user_id')

        # 验证必要字段
        required_fields = ['community_id', 'rule_name']
        for field in required_fields:
            if not data.get(field):
                return make_err_response({}, f'缺少必要字段: {field}')

        rule = CommunityCheckinRuleService.create_community_rule(data, community_id, created_by)

        response_data = {
            'community_rule_id': rule.community_rule_id,
            'community_id': rule.community_id,
            'rule_name': rule.rule_name,
            'status': rule.status,
            'created_by': rule.created_by,
            'created_at': rule.created_at.isoformat() if rule.created_at else None
        }

        logger.info(f"创建社区规则成功: 规则ID={rule.community_rule_id}, 创建者={created_by}")
        return make_succ_response(response_data, '创建社区规则成功')

    except ValueError as e:
        logger.warning(f"创建社区规则参数错误: {str(e)}")
        return make_err_response({}, str(e))
    except Exception as e:
        logger.error(f"创建社区规则失败: {str(e)}")
        return make_err_response({}, f'创建社区规则失败: {str(e)}')


@app.route('/api/community-checkin/rules/<int:rule_id>', methods=['PUT'])
@login_required
@community_permission_required
def update_community_rule(decoded, rule_id):
    """
    修改社区规则（仅限未启用状态）
    PUT /api/community-checkin/rules/<rule_id>

    Request Body:
    {
        "rule_name": "更新后的规则名称",
        "icon_url": "...",
        "frequency_type": 1,
        "time_slot_type": 1,
        "custom_time": "10:00:00"
    }

    Response:
    {
        "code": 1,
        "msg": "修改社区规则成功",
        "data": {
            "community_rule_id": 1,
            "rule_name": "更新后的规则名称",
            "updated_by": 123,
            "updated_at": "2025-12-19T11:00:00"
        }
    }
    """
    try:
        data = request.get_json()
        updated_by = decoded.get('user_id')

        rule = CommunityCheckinRuleService.update_community_rule(rule_id, data, updated_by)

        response_data = {
            'community_rule_id': rule.community_rule_id,
            'rule_name': rule.rule_name,
            'status': rule.status,
            'updated_by': rule.updated_by,
            'updated_at': rule.updated_at.isoformat() if rule.updated_at else None
        }

        logger.info(f"修改社区规则成功: 规则ID={rule_id}, 更新者={updated_by}")
        return make_succ_response(response_data, '修改社区规则成功')

    except ValueError as e:
        logger.warning(f"修改社区规则失败: {str(e)}")
        return make_err_response({}, str(e))
    except Exception as e:
        logger.error(f"修改社区规则失败: {str(e)}")
        return make_err_response({}, f'修改社区规则失败: {str(e)}')


@app.route('/api/community-checkin/rules/<int:rule_id>/enable', methods=['POST'])
@login_required
@community_permission_required
def enable_community_rule(decoded, rule_id):
    """
    启用社区规则
    POST /api/community-checkin/rules/<rule_id>/enable

    Response:
    {
        "code": 1,
        "msg": "规则已启用",
        "data": {
            "community_rule_id": 1,
            "is_enabled": true,
            "enabled_at": "2025-12-19T10:00:00",
            "enabled_by": 123
        }
    }
    """
    try:
        enabled_by = decoded.get('user_id')

        rule_dict = CommunityCheckinRuleService.enable_community_rule(rule_id, enabled_by)

        response_data = {
            'community_rule_id': rule_dict['community_rule_id'],
            'community_id': rule_dict['community_id'],
            'status': rule_dict['status'],
            'enabled_at': rule_dict['enabled_at'],
            'enabled_by': rule_dict['enabled_by']
        }

        logger.info(f"启用社区规则成功: 规则ID={rule_id}, 启用人={enabled_by}")
        return make_succ_response(response_data, '规则已启用')

    except ValueError as e:
        logger.warning(f"启用社区规则失败: {str(e)}")
        return make_err_response({}, str(e))
    except Exception as e:
        logger.error(f"启用社区规则失败: {str(e)}")
        return make_err_response({}, f'启用社区规则失败: {str(e)}')


@app.route('/api/community-checkin/rules/<int:rule_id>/disable', methods=['POST'])
@login_required
@community_permission_required
def disable_community_rule(decoded, rule_id):
    """
    停用社区规则
    POST /api/community-checkin/rules/<rule_id>/disable

    Response:
    {
        "code": 1,
        "msg": "规则已停用",
        "data": {
            "community_rule_id": 1,
            "is_enabled": false,
            "disabled_at": "2025-12-19T11:00:00",
            "disabled_by": 123
        }
    }
    """
    try:
        disabled_by = decoded.get('user_id')

        rule_dict = CommunityCheckinRuleService.disable_community_rule(rule_id, disabled_by)

        response_data = {
            'community_rule_id': rule_dict['community_rule_id'],
            'status': rule_dict['status'],
            'disabled_at': rule_dict['disabled_at'],
            'disabled_by': rule_dict['disabled_by']
        }

        logger.info(f"停用社区规则成功: 规则ID={rule_id}, 停用人={disabled_by}")
        return make_succ_response(response_data, '规则已停用')

    except ValueError as e:
        logger.warning(f"停用社区规则失败: {str(e)}")
        return make_err_response({}, str(e))
    except Exception as e:
        logger.error(f"停用社区规则失败: {str(e)}")
        return make_err_response({}, f'停用社区规则失败: {str(e)}')


@app.route('/api/community-checkin/rules/<int:rule_id>', methods=['DELETE'])
@login_required
@community_permission_required
def delete_community_rule(decoded, rule_id):
    """
    删除社区规则（仅限未启用状态）
    DELETE /api/community-checkin/rules/<rule_id>

    Response:
    {
        "code": 1,
        "msg": "删除社区规则成功",
        "data": {}
    }
    """
    try:
        deleted_by = decoded.get('user_id')

        CommunityCheckinRuleService.delete_community_rule(rule_id, deleted_by)

        logger.info(f"删除社区规则成功: 规则ID={rule_id}, 删除者={deleted_by}")
        return make_succ_response({}, '删除社区规则成功')

    except ValueError as e:
        logger.warning(f"删除社区规则失败: {str(e)}")
        return make_err_response({}, str(e))
    except Exception as e:
        logger.error(f"删除社区规则失败: {str(e)}")
        return make_err_response({}, f'删除社区规则失败: {str(e)}')


@app.route('/api/community-checkin/rules/<int:rule_id>', methods=['GET'])
@login_required
def get_community_rule_detail(decoded, rule_id):
    """
    获取社区规则详情
    GET /api/community-checkin/rules/<rule_id>

    Response:
    {
        "code": 1,
        "msg": "success",
        "data": {
            "community_rule_id": 1,
            "community_id": 1,
            "rule_name": "每日健康打卡",
            "icon_url": "...",
            "frequency_type": 0,
            "time_slot_type": 4,
            "custom_time": "09:00:00",
            "is_enabled": false,
            "status": 1,
            "created_by": 123,
            "updated_by": 123,
            "created_at": "2025-12-19T10:00:00",
            "updated_at": "2025-12-19T10:00:00",
            "community_name": "安卡大家庭",
            "created_by_name": "张主管",
            "updated_by_name": "张主管"
        }
    }
    """
    try:
        rule_dict = CommunityCheckinRuleService.get_rule_detail(rule_id)

        # 检查用户是否有权限查看（用户需要属于该社区）
        user_id = decoded.get('user_id')
        # 需要从数据库获取用户信息来检查社区
        from wxcloudrun.user_service import UserService
        user = UserService.query_user_by_id(user_id)
        user_community = user.community_id if user and hasattr(user, 'community_id') else None

        if user_community != rule_dict['community_id']:
            # 如果不是该社区用户，检查是否有社区管理权限
            from wxcloudrun.community_service import CommunityService
            if not CommunityService.has_community_permission(user.user_id, rule_dict['community_id']):
                return make_err_response({}, '无权限查看此规则')
        if rule_dict['status'] == 2:
            return make_err_response({}, '此规则已删除')

        logger.info(f"获取社区规则详情成功: 规则ID={rule_id}")
        return make_succ_response(rule_dict)

    except ValueError as e:
        logger.warning(f"获取社区规则详情失败: {str(e)}")
        return make_err_response({}, str(e))
    except Exception as e:
        logger.error(f"获取社区规则详情失败: {str(e)}")
        return make_err_response({}, f'获取社区规则详情失败: {str(e)}')