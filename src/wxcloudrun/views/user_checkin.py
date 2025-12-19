"""
用户打卡规则视图模块
处理用户规则查询和聚合的HTTP请求（个人规则 + 社区规则）
"""
import logging
from flask import request, g
from wxcloudrun import app
from wxcloudrun.decorators import login_required
from wxcloudrun.user_checkin_rule_service import UserCheckinRuleService
from wxcloudrun.response import make_succ_response, make_err_response

logger = logging.getLogger('UserCheckinView')


@app.route('/api/user-checkin/rules', methods=['GET'])
@login_required
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
                // 个人规则
                "rule_id": 1,
                "rule_name": "个人每日阅读",
                "icon_url": "...",
                "frequency_type": 0,
                "time_slot_type": 4,
                "custom_time": "20:00:00",
                "rule_source": "personal",
                "is_editable": true,
                "source_label": "个人规则"
            },
            {
                // 社区规则
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
            }
        ]
    }
    """
    try:
        user_id = g.user.user_id
        
        rules = UserCheckinRuleService.get_user_all_rules(user_id)
        
        logger.info(f"获取用户所有规则成功: 用户ID={user_id}, 规则数量={len(rules)}")
        return make_success_response(rules)
        
    except Exception as e:
        logger.error(f"获取用户所有规则失败: {str(e)}")
        return make_err_response({}, f'获取用户所有规则失败: {str(e)}')


@app.route('/api/user-checkin/today-plan', methods=['GET'])
@login_required
def get_user_today_plan():
    """
    获取用户今日打卡计划（混合个人规则和社区规则）
    GET /api/user-checkin/today-plan
    
    Response:
    {
        "code": 1,
        "msg": "success",
        "data": [
            {
                "rule_id": 1,
                "rule_name": "个人每日阅读",
                "icon_url": "...",
                "planned_time": "2025-12-19T20:00:00",
                "status": "unchecked",
                "checkin_time": null,
                "rule_source": "personal",
                "is_editable": true
            },
            {
                "rule_id": 1,
                "rule_name": "社区健康打卡",
                "icon_url": "...",
                "planned_time": "2025-12-19T09:00:00",
                "status": "checked",
                "checkin_time": "2025-12-19T09:05:00",
                "rule_source": "community",
                "is_editable": false,
                "community_name": "安卡大家庭"
            }
        ]
    }
    """
    try:
        user_id = g.user.user_id
        
        today_plan = UserCheckinRuleService.get_today_checkin_plan(user_id)
        
        logger.info(f"获取用户今日计划成功: 用户ID={user_id}, 事项数量={len(today_plan)}")
        return make_success_response(today_plan)
        
    except Exception as e:
        logger.error(f"获取用户今日计划失败: {str(e)}")
        return make_err_response({}, f'获取用户今日计划失败: {str(e)}')


@app.route('/api/user-checkin/rules/<int:rule_id>', methods=['GET'])
@login_required
def get_user_rule_detail(rule_id):
    """
    获取用户规则详情（根据规则来源）
    GET /api/user-checkin/rules/<rule_id>?rule_source=<personal/community>
    
    Query Parameters:
    - rule_source: 规则来源（personal/community），默认为personal
    
    Response:
    {
        "code": 1,
        "msg": "success",
        "data": {
            // 个人规则或社区规则的详情
            "rule_source": "personal",
            "is_editable": true,
            // ... 其他规则字段
        }
    }
    """
    try:
        user_id = g.user.user_id
        rule_source = request.args.get('rule_source', 'personal')
        
        rule_detail = UserCheckinRuleService.get_rule_by_id(rule_id, user_id, rule_source)
        
        logger.info(f"获取用户规则详情成功: 用户ID={user_id}, 规则ID={rule_id}, 规则来源={rule_source}")
        return make_success_response(rule_detail)
        
    except ValueError as e:
        logger.warning(f"获取用户规则详情失败: {str(e)}")
        return make_err_response({}, str(e))
    except Exception as e:
        logger.error(f"获取用户规则详情失败: {str(e)}")
        return make_err_response({}, f'获取用户规则详情失败: {str(e)}')


@app.route('/api/user-checkin/statistics', methods=['GET'])
@login_required
def get_user_rules_statistics():
    """
    获取用户规则统计信息
    GET /api/user-checkin/statistics
    
    Response:
    {
        "code": 1,
        "msg": "success",
        "data": {
            "personal_rule_count": 3,
            "community_rule_count": 2,
            "total_rule_count": 5,
            "today_checkin_count": 4,
            "personal_percentage": 60.0,
            "community_percentage": 40.0
        }
    }
    """
    try:
        user_id = g.user.user_id
        
        statistics = UserCheckinRuleService.get_user_rules_statistics(user_id)
        
        logger.info(f"获取用户规则统计成功: 用户ID={user_id}")
        return make_success_response(statistics)
        
    except Exception as e:
        logger.error(f"获取用户规则统计失败: {str(e)}")
        return make_err_response({}, f'获取用户规则统计失败: {str(e)}')


@app.route('/api/user-checkin/rules/source-info', methods=['POST'])
@login_required
def get_rules_source_info():
    """
    批量获取规则来源信息
    POST /api/user-checkin/rules/source-info
    
    Request Body:
    {
        "rules": [
            {
                "rule_id": 1,
                "rule_source": "personal"
            },
            {
                "rule_id": 2,
                "rule_source": "community"
            }
        ]
    }
    
    Response:
    {
        "code": 1,
        "msg": "success",
        "data": [
            {
                "rule_id": 1,
                "rule_source": "personal",
                "is_editable": true,
                "source_label": "个人规则"
            },
            {
                "rule_id": 2,
                "rule_source": "community",
                "is_editable": false,
                "source_label": "社区规则",
                "community_name": "安卡大家庭",
                "is_enabled": true
            }
        ]
    }
    """
    try:
        user_id = g.user.user_id
        data = request.get_json()
        rules_data = data.get('rules', [])
        
        source_infos = []
        for rule_info in rules_data:
            rule_id = rule_info.get('rule_id')
            rule_source = rule_info.get('rule_source', 'personal')
            
            try:
                rule_detail = UserCheckinRuleService.get_rule_by_id(rule_id, user_id, rule_source)
                source_info = {
                    'rule_id': rule_id,
                    'rule_source': rule_source,
                    'is_editable': rule_detail.get('is_editable', False),
                    'source_label': '个人规则' if rule_source == 'personal' else '社区规则'
                }
                
                if rule_source == 'community':
                    source_info['community_name'] = rule_detail.get('community_name')
                    source_info['is_enabled'] = rule_detail.get('is_enabled', False)
                
                source_infos.append(source_info)
            except ValueError:
                # 如果规则不存在或无权限，跳过
                continue
        
        logger.info(f"批量获取规则来源信息成功: 用户ID={user_id}, 规则数量={len(source_infos)}")
        return make_success_response(source_infos)
        
    except Exception as e:
        logger.error(f"批量获取规则来源信息失败: {str(e)}")
        return make_err_response({}, f'批量获取规则来源信息失败: {str(e)}')