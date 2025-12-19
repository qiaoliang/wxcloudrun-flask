"""
用户打卡规则服务模块
处理用户规则查询和聚合逻辑（个人规则 + 社区规则）
"""
import logging
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from database.models import CheckinRule, CommunityCheckinRule, UserCommunityRule, User, db
from wxcloudrun.checkin_rule_service import CheckinRuleService
from wxcloudrun.community_checkin_rule_service import CommunityCheckinRuleService

logger = logging.getLogger('UserCheckinRuleService')


class UserCheckinRuleService:
    """用户打卡规则服务类"""
    
    @staticmethod
    def get_user_all_rules(user_id):
        """
        获取用户所有打卡规则（个人规则 + 社区规则）
        
        Args:
            user_id: 用户ID
            
        Returns:
            list: 规则列表，每个规则包含来源信息
        """
        try:
            all_rules = []
            
            # 获取个人规则
            personal_rules = CheckinRuleService.query_rules_by_user_id(user_id)
            for rule in personal_rules:
                rule_dict = rule.to_dict()
                rule_dict['rule_source'] = 'personal'
                rule_dict['is_editable'] = True
                all_rules.append(rule_dict)
            
            # 获取社区规则
            community_rules = CommunityCheckinRuleService.get_user_community_rules(user_id)
            for rule in community_rules:
                rule_dict = rule.to_dict()
                rule_dict['rule_source'] = 'community'
                rule_dict['is_editable'] = False
                
                # 添加社区信息
                if rule.community:
                    rule_dict['community_name'] = rule.community.name
                
                # 添加创建者信息
                if rule.creator:
                    rule_dict['created_by_name'] = rule.creator.nickname or rule.creator.phone
                
                all_rules.append(rule_dict)
            
            logger.info(f"获取用户所有规则成功: 用户ID={user_id}, 规则总数={len(all_rules)}")
            return all_rules
            
        except SQLAlchemyError as e:
            logger.error(f"获取用户所有规则失败: {str(e)}")
            raise
    
    @staticmethod
    def get_today_checkin_plan(user_id):
        """
        获取用户今日打卡计划（混合个人规则和社区规则）
        
        Args:
            user_id: 用户ID
            
        Returns:
            list: 今日打卡事项列表
        """
        try:
            today_plan = []
            
            # 获取个人规则的今日计划
            personal_plan = CheckinRuleService.get_today_checkin_plan(user_id)
            for item in personal_plan:
                item['rule_source'] = 'personal'
                item['is_editable'] = True
                today_plan.append(item)
            
            # 获取社区规则的今日计划
            community_rules = CommunityCheckinRuleService.get_user_community_rules(user_id)
            today = datetime.now().date()
            
            for rule in community_rules:
                # 检查今天是否需要打卡
                if not CheckinRuleService._should_checkin_today(rule, today):
                    continue
                
                # 获取今日打卡记录
                from database.models import CheckinRecord
                today_records = (db.session.query(CheckinRecord)
                                .filter(
                                    CheckinRecord.rule_id == rule.community_rule_id,
                                    db.func.date(CheckinRecord.planned_time) == today,
                                    CheckinRecord.solo_user_id == user_id
                                )
                                .all())
                
                # 计算计划时间
                planned_time = CheckinRuleService._calculate_planned_time(rule, today)
                
                # 确定打卡状态
                status_info = CheckinRuleService._determine_checkin_status(today_records)
                
                plan_item = {
                    'rule_id': rule.community_rule_id,
                    'rule_name': rule.rule_name,
                    'icon_url': rule.icon_url,
                    'planned_time': planned_time.isoformat() if planned_time else None,
                    'status': status_info['status'],
                    'checkin_time': status_info['checkin_time'],
                    'rule_source': 'community',
                    'is_editable': False,
                    'community_name': rule.community.name if rule.community else None
                }
                
                today_plan.append(plan_item)
            
            # 按计划时间排序
            today_plan.sort(key=lambda x: x['planned_time'] or '')
            
            logger.info(f"获取用户今日计划成功: 用户ID={user_id}, 事项数量={len(today_plan)}")
            return today_plan
            
        except SQLAlchemyError as e:
            logger.error(f"获取用户今日计划失败: {str(e)}")
            raise
    
    @staticmethod
    def get_rule_by_id(rule_id, user_id, rule_source='personal'):
        """
        根据规则ID和来源获取规则详情
        
        Args:
            rule_id: 规则ID
            user_id: 用户ID
            rule_source: 规则来源（personal/community）
            
        Returns:
            dict: 规则详情
            
        Raises:
            ValueError: 规则不存在或无权限
        """
        try:
            if rule_source == 'personal':
                # 获取个人规则
                rule = CheckinRuleService.query_rule_by_id(rule_id)
                if not rule or rule.solo_user_id != user_id:
                    raise ValueError('个人规则不存在或无权限')
                
                rule_dict = rule.to_dict()
                rule_dict['rule_source'] = 'personal'
                rule_dict['is_editable'] = True
                
            elif rule_source == 'community':
                # 获取社区规则
                rule = CommunityCheckinRuleService.get_rule_detail(rule_id)
                
                # 检查用户是否有权限查看此规则
                user = User.query.get(user_id)
                if not user or user.community_id != rule.community_id:
                    raise ValueError('社区规则不存在或无权限')
                
                # 检查规则是否对用户生效
                mapping = UserCommunityRule.query.filter_by(
                    user_id=user_id,
                    community_rule_id=rule_id,
                    is_active=True
                ).first()
                
                if not mapping:
                    raise ValueError('此规则未对您生效')
                
                rule_dict = rule.to_dict()
                rule_dict['rule_source'] = 'community'
                rule_dict['is_editable'] = False
                
                # 添加额外信息
                if rule.community:
                    rule_dict['community_name'] = rule.community.name
                if rule.creator:
                    rule_dict['created_by_name'] = rule.creator.nickname or rule.creator.phone
                if rule.updater:
                    rule_dict['updated_by_name'] = rule.updater.nickname or rule.updater.phone
                
            else:
                raise ValueError(f'不支持的规则来源: {rule_source}')
            
            return rule_dict
            
        except SQLAlchemyError as e:
            logger.error(f"获取规则详情失败: {str(e)}")
            raise
    
    @staticmethod
    def get_rule_source_info(rule):
        """
        获取规则来源信息
        
        Args:
            rule: 规则对象（CheckinRule或CommunityCheckinRule）
            
        Returns:
            dict: 来源信息
        """
        if isinstance(rule, CheckinRule):
            return {
                'rule_source': 'personal',
                'is_editable': True,
                'source_label': '个人规则'
            }
        elif isinstance(rule, CommunityCheckinRule):
            return {
                'rule_source': 'community',
                'is_editable': False,
                'source_label': '社区规则',
                'community_name': rule.community.name if rule.community else None,
                'is_enabled': rule.is_enabled
            }
        else:
            return {
                'rule_source': 'unknown',
                'is_editable': False,
                'source_label': '未知来源'
            }
    
    @staticmethod
    def get_user_rules_statistics(user_id):
        """
        获取用户规则统计信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            dict: 统计信息
        """
        try:
            # 获取个人规则数量
            personal_rules = CheckinRuleService.query_rules_by_user_id(user_id)
            personal_count = len(personal_rules)
            
            # 获取社区规则数量
            community_rules = CommunityCheckinRuleService.get_user_community_rules(user_id)
            community_count = len(community_rules)
            
            # 获取今日需要打卡的规则数量
            today_plan = UserCheckinRuleService.get_today_checkin_plan(user_id)
            today_count = len(today_plan)
            
            statistics = {
                'personal_rule_count': personal_count,
                'community_rule_count': community_count,
                'total_rule_count': personal_count + community_count,
                'today_checkin_count': today_count,
                'personal_percentage': round(personal_count / max(personal_count + community_count, 1) * 100, 1),
                'community_percentage': round(community_count / max(personal_count + community_count, 1) * 100, 1)
            }
            
            logger.info(f"获取用户规则统计成功: 用户ID={user_id}, 统计信息={statistics}")
            return statistics
            
        except SQLAlchemyError as e:
            logger.error(f"获取用户规则统计失败: {str(e)}")
            raise