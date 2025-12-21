"""
用户打卡规则服务模块
处理用户规则查询和聚合逻辑（个人规则 + 社区规则）
"""
import logging
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from wxcloudrun.dao import get_db
from database.models import CheckinRule, CommunityCheckinRule, UserCommunityRule, User
from wxcloudrun.checkin_rule_service import CheckinRuleService
from wxcloudrun.community_checkin_rule_service import CommunityCheckinRuleService
from wxcloudrun.checkin_record_service import CheckinRecordService

logger = logging.getLogger('UserCheckinRuleService')


class UserCheckinRuleService:
    """用户打卡规则服务类"""

    @staticmethod
    def get_user_all_rules(user_id,session = None):
        """
        获取用户所有打卡规则（社区规则优先，个人规则在后）

        Args:
            user_id: 用户ID

        Returns:
            list: 规则列表，每个规则包含来源信息，社区规则在前，个人规则在后
        """
        try:
            all_rules = []

            # 获取用户所属社区的所有规则（包括启用和停用的）
            community_rules = UserCheckinRuleService._get_user_all_community_rules(user_id)
            for rule in community_rules:
                rule_dict = rule.to_dict()
                rule_dict['rule_source'] = 'community'
                rule_dict['is_editable'] = False  # 社区规则用户不可编辑
                rule_dict['source_label'] = '社区规则'

                # 添加社区信息
                if rule.community:
                    rule_dict['community_name'] = rule.community.name
                    rule_dict['source_label'] = f'社区规则 ({rule.community.name})'

                # 添加创建者信息
                if rule.creator:
                    rule_dict['created_by_name'] = rule.creator.nickname or rule.creator.phone

                # 根据规则状态和用户映射状态判断是否对用户激活
                is_rule_enabled = rule_dict.get('status') == 1
                is_user_mapping_active = rule_dict.get('is_user_mapping_active', False)
                rule_dict['is_active_for_user'] = is_rule_enabled and is_user_mapping_active
                
                # 添加规则状态描述
                if is_rule_enabled and is_user_mapping_active:
                    rule_dict['status_label'] = '启用'
                elif not is_rule_enabled:
                    rule_dict['status_label'] = '停用'
                else:
                    rule_dict['status_label'] = '未激活'

                all_rules.append(rule_dict)

            # 获取个人规则（在社区规则后显示）
            personal_rules = CheckinRuleService.query_rules_by_user_id(user_id)
            for rule in personal_rules:
                rule_dict = rule.to_dict()
                rule_dict['rule_source'] = 'personal'
                rule_dict['is_editable'] = True
                rule_dict['source_label'] = '个人规则'
                rule_dict['is_active_for_user'] = True  # 个人规则默认对用户激活
                rule_dict['status_label'] = '启用'
                all_rules.append(rule_dict)

            logger.info(f"获取用户所有规则成功: 用户ID={user_id}, 规则总数={len(all_rules)}")
            return all_rules

        except SQLAlchemyError as e:
            logger.error(f"获取用户所有规则失败: {str(e)}")
            raise

    @staticmethod
    def _get_user_active_community_rules(user_id):
        """
        获取用户激活的社区规则
        
        Args:
            user_id: 用户ID
            
        Returns:
            list: 激活的社区规则列表
        """
        try:
            from wxcloudrun.dao import get_db
            
            with get_db().get_session() as session:
                # 通过UserCommunityRule表查询激活的社区规则
                active_rules = session.query(CommunityCheckinRule).join(UserCommunityRule).filter(
                    UserCommunityRule.user_id == user_id,
                    UserCommunityRule.is_active == True,
                    CommunityCheckinRule.status == 1  # 社区规则本身也是启用状态
                ).all()
                
                # 预加载关联数据以避免会话问题
                for rule in active_rules:
                    # 预加载社区和创建者信息
                    if hasattr(rule, 'community'):
                        _ = rule.community.name if rule.community else None
                    if hasattr(rule, 'creator'):
                        _ = rule.creator.nickname if rule.creator else None
                
                # 将对象转换为字典，避免会话绑定问题
                result = []
                for rule in active_rules:
                    rule_dict = rule.to_dict()
                    # 添加关联信息
                    if rule.community:
                        rule_dict['community_name'] = rule.community.name
                    if rule.creator:
                        rule_dict['created_by_name'] = rule.creator.nickname or rule.creator.phone
                    
                    # 创建一个简单的对象来保持兼容性
                    class RuleWrapper:
                        def __init__(self, data):
                            self._data = data
                            # 添加必要的属性
                            self.community_rule_id = data.get('community_rule_id')
                            self.rule_name = data.get('rule_name')
                            self.icon_url = data.get('icon_url')
                            self.frequency_type = data.get('frequency_type')
                            self.time_slot_type = data.get('time_slot_type')
                            self.custom_time = data.get('custom_time')
                            self.custom_start_date = data.get('custom_start_date')
                            self.custom_end_date = data.get('custom_end_date')
                            self.week_days = data.get('week_days')
                        
                        def to_dict(self):
                            return self._data.copy()
                        
                        @property
                        def community(self):
                            class CommunityWrapper:
                                def __init__(self, name):
                                    self.name = name
                            return CommunityWrapper(self._data.get('community_name'))
                        
                        @property
                        def creator(self):
                            class CreatorWrapper:
                                def __init__(self, nickname, phone):
                                    self.nickname = nickname
                                    self.phone = phone
                            return CreatorWrapper(
                                self._data.get('created_by_name'),
                                self._data.get('creator_phone')
                            )
                    
                    result.append(RuleWrapper(rule_dict))
                
                return result
                
        except SQLAlchemyError as e:
            logger.error(f"获取用户激活社区规则失败: {str(e)}")
            raise

    @staticmethod
    def _get_user_all_community_rules(user_id):
        """
        获取用户所属社区的所有规则（包括启用和停用的）
        
        Args:
            user_id: 用户ID
            
        Returns:
            list: 所有社区规则列表（包含激活状态信息）
        """
        try:
            from wxcloudrun.dao import get_db
            
            with get_db().get_session() as session:
                # 获取用户信息
                user = session.query(User).get(user_id)
                if not user or not user.community_id:
                    return []
                
                # 查询用户所属社区的所有规则（包括启用和停用的）
                all_rules = session.query(CommunityCheckinRule).filter(
                    CommunityCheckinRule.community_id == user.community_id,
                    CommunityCheckinRule.status != 2  # 排除已删除的规则
                ).all()
                
                # 获取该用户的规则映射记录
                user_mappings = {}
                mappings = session.query(UserCommunityRule).filter(
                    UserCommunityRule.user_id == user_id
                ).all()
                
                for mapping in mappings:
                    user_mappings[mapping.community_rule_id] = mapping.is_active
                
                # 确保当前社区的所有已启用规则都有映射记录
                enabled_rules = [rule for rule in all_rules if rule.status == 1]
                for rule in enabled_rules:
                    if rule.community_rule_id not in user_mappings:
                        # 如果已启用规则没有映射记录，说明是数据不一致，自动创建映射
                        new_mapping = UserCommunityRule(
                            user_id=user_id,
                            community_rule_id=rule.community_rule_id,
                            is_active=True,
                            created_at=datetime.now()
                        )
                        session.add(new_mapping)
                        user_mappings[rule.community_rule_id] = True
                        
                # 提交新创建的映射记录
                if any(rule.community_rule_id not in [m.community_rule_id for m in mappings] 
                      for rule in enabled_rules):
                    session.commit()
                
                # 预加载关联数据并添加状态信息
                result = []
                for rule in all_rules:
                    # 预加载社区和创建者信息
                    if hasattr(rule, 'community'):
                        _ = rule.community.name if rule.community else None
                    if hasattr(rule, 'creator'):
                        _ = rule.creator.nickname if rule.creator else None
                    
                    # 创建规则字典并添加用户映射状态
                    rule_dict = rule.to_dict()
                    rule_dict['is_user_mapping_active'] = user_mappings.get(rule.community_rule_id, False)
                    
                    # 创建一个简单的对象来保持兼容性
                    class RuleWrapper:
                        def __init__(self, data):
                            self._data = data
                        
                        def to_dict(self):
                            return self._data.copy()
                        
                        @property
                        def community(self):
                            class CommunityWrapper:
                                def __init__(self, name):
                                    self.name = name
                            return CommunityWrapper(self._data.get('community_name'))
                        
                        @property
                        def creator(self):
                            class CreatorWrapper:
                                def __init__(self, nickname, phone):
                                    self.nickname = nickname
                                    self.phone = phone
                            return CreatorWrapper(
                                self._data.get('created_by_name'),
                                self._data.get('creator_phone')
                            )
                    
                    result.append(RuleWrapper(rule_dict))
                
                return result
                
        except SQLAlchemyError as e:
            logger.error(f"获取用户所有社区规则失败: {str(e)}")
            raise

    @staticmethod
    def get_today_checkin_plan(user_id,session = None):
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
            personal_plan_result = CheckinRuleService.get_today_checkin_plan(user_id)
            if isinstance(personal_plan_result, dict) and 'checkin_items' in personal_plan_result:
                personal_plan = personal_plan_result['checkin_items']
            else:
                personal_plan = []
            
            for item in personal_plan:
                item['rule_source'] = 'personal'
                item['is_editable'] = True
                today_plan.append(item)

            # 获取激活的社区规则的今日计划
            community_rules = UserCheckinRuleService._get_user_active_community_rules(user_id)
            today = datetime.now().date()

            for rule in community_rules:
                # 检查今天是否需要打卡
                if not CheckinRuleService._should_checkin_today(rule, today):
                    continue

                # 获取今日打卡记录
                from database.models import CheckinRecord
                from sqlalchemy import func
                with get_db().get_session() as session:
                    today_records = (session.query(CheckinRecord)
                                .filter(
                                    CheckinRecord.rule_id == rule.community_rule_id,
                                    func.date(CheckinRecord.planned_time) == today,
                                    CheckinRecord.solo_user_id == user_id
                                )
                                .all())

                # 计算计划时间
                planned_time = CheckinRecordService._calculate_planned_time(rule, today)

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
    def get_rule_by_id(rule_id, user_id, rule_source='personal',session = None):
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
                if not user or user.community_id != rule['community_id']:
                    raise ValueError('社区规则不存在或无权限')

                # 检查规则是否对用户生效
                mapping = UserCommunityRule.query.filter_by(
                    user_id=user_id,
                    community_rule_id=rule_id,
                    is_active=True
                ).first()

                if not mapping:
                    raise ValueError('此规则未对您生效')

                rule_dict = rule.copy()  # rule已经是字典，直接复制
                rule_dict['rule_source'] = 'community'
                rule_dict['is_editable'] = False

                # 添加额外信息（rule字典中已经包含了这些信息）
                if rule.get('community'):
                    rule_dict['community_name'] = rule['community']['name']
                if rule.get('creator'):
                    rule_dict['created_by_name'] = rule['creator']['nickname'] or rule['creator']['phone']
                if rule.get('updater'):
                    rule_dict['updated_by_name'] = rule['updater']['nickname'] or rule['updater']['phone']

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
                'status': rule.status
            }
        else:
            return {
                'rule_source': 'unknown',
                'is_editable': False,
                'source_label': '未知来源'
            }

    @staticmethod
    def get_user_rules_statistics(user_id,session = None):
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