"""
用户打卡规则服务模块
处理用户规则查询和聚合逻辑（个人规则 + 社区规则）
"""
import logging
from datetime import datetime, date, time
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import noload, joinedload
from database.flask_models import db, CheckinRule, CommunityCheckinRule, UserCommunityRule, User, CheckinRecord
from app.shared.utils.community_helpers import CommunityRuleQueryHelper
from wxcloudrun.utils.timeutil import parse_time_only, parse_date_only
from app.shared.utils.transaction import transaction

logger = logging.getLogger('UserCheckinRuleService')


class UserCheckinRuleService:
    """用户打卡规则服务类"""

    @staticmethod
    def get_user_all_rules(user_id):
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

            # 获取用户的规则映射状态
            user_mappings = {}
            # 使用 SQLAlchemy 2.0 的 select() 语句
            stmt_mappings = select(UserCommunityRule).where(
                UserCommunityRule.user_id == user_id
            )
            mappings = db.session.execute(stmt_mappings).scalars().all()
            for mapping in mappings:
                user_mappings[mapping.community_rule_id] = mapping.is_active

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
                is_user_mapping_active = user_mappings.get(rule.community_rule_id, False)
                rule_dict['is_user_mapping_active'] = is_user_mapping_active
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
            personal_rules = UserCheckinRuleService.query_rules_by_user_id(user_id)
            logger.info(f"获取个人规则: 用户ID={user_id}, 规则数量={len(personal_rules)}")
            for rule in personal_rules:
                rule_dict = rule.to_dict()
                rule_dict['rule_source'] = 'personal'
                rule_dict['is_editable'] = True
                rule_dict['source_label'] = '个人规则'
                rule_dict['is_active_for_user'] = True  # 个人规则默认对用户激活
                rule_dict['status_label'] = '启用'
                all_rules.append(rule_dict)

            logger.info(f"获取用户所有规则成功: 用户ID={user_id}, 规则总数={len(all_rules)}")
            return {'rules': all_rules}

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
            # 使用 SQLAlchemy 2.0 的 select() 语句
            # 通过UserCommunityRule表查询激活的社区规则
            stmt = select(CommunityCheckinRule).join(UserCommunityRule).where(
                UserCommunityRule.user_id == user_id,
                UserCommunityRule.is_active == True,
                CommunityCheckinRule.status == 1  # 社区规则本身也是启用状态
            )
            active_rules = db.session.execute(stmt).scalars().all()

            # Flask-SQLAlchemy 自动处理会话，不需要复杂的对象包装
            return active_rules

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
            # 获取用户信息
            user = db.session.get(User, user_id)
            if not user or not user.community_id:
                return []

            # 使用 SQLAlchemy 2.0 的 select() 语句
            # 查询用户所属社区的所有规则（包括启用和停用的）
            # 使用 joinedload 预加载关系，避免 N+1 查询问题
            from sqlalchemy.orm import joinedload
            stmt_all_rules = select(CommunityCheckinRule).options(
                joinedload(CommunityCheckinRule.community),
                joinedload(CommunityCheckinRule.creator)
            ).where(
                CommunityCheckinRule.community_id == user.community_id,
                CommunityCheckinRule.status != 2  # 排除已删除的规则
            )
            all_rules = db.session.execute(stmt_all_rules).scalars().all()

            # 获取该用户的规则映射记录
            user_mappings = {}
            stmt_mappings = select(UserCommunityRule).where(
                UserCommunityRule.user_id == user_id
            )
            mappings = db.session.execute(stmt_mappings).scalars().all()

            for mapping in mappings:
                user_mappings[mapping.community_rule_id] = mapping.is_active

            # 确保当前社区的所有已启用规则都有映射记录
            enabled_rules = [rule for rule in all_rules if rule.status == 1]
            new_mappings_created = False

            for rule in enabled_rules:
                if rule.community_rule_id not in user_mappings:
                    # 如果已启用规则没有映射记录，说明是数据不一致，自动创建映射
                    new_mapping = UserCommunityRule(
                        user_id=user_id,
                        community_rule_id=rule.community_rule_id,
                        is_active=True,
                        created_at=datetime.now()
                    )
                    db.session.add(new_mapping)
                    user_mappings[rule.community_rule_id] = True
                    new_mappings_created = True

            # 提交新创建的映射记录
            if new_mappings_created:
                with transaction():
                    db.session.flush()

            # 返回规则列表
            return all_rules

        except SQLAlchemyError as e:
            logger.error(f"获取用户所有社区规则失败: {str(e)}")
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
            personal_plan_result = UserCheckinRuleService.get_today_checkin_plan_personal(user_id)
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
                if not UserCheckinRuleService._should_checkin_today(rule, today):
                    continue

                # 使用 SQLAlchemy 2.0 的 select() 语句
                # 获取今日打卡记录
                from sqlalchemy import func
                from sqlalchemy.orm import noload
                
                stmt = select(CheckinRecord).options(
                    noload(CheckinRecord.user),
                    noload(CheckinRecord.solo_user),
                    noload(CheckinRecord.rule)
                ).where(
                    CheckinRecord.rule_id == rule.community_rule_id,
                    func.date(CheckinRecord.checkin_time) == today,  # 更新字段名
                    CheckinRecord.user_id == user_id  # 更新字段名
                )
                today_records = db.session.execute(stmt).scalars().all()

                # 计算计划时间 - 使用规则的时间设置
                planned_time = UserCheckinRuleService._calculate_planned_time(rule, today)

                # 确定打卡状态
                status_info = UserCheckinRuleService._determine_checkin_status(today_records)

                plan_item = {
                    'rule_id': rule.community_rule_id,
                    'rule_name': rule.rule_name,
                    'icon_url': rule.icon_url,
                    'planned_time': planned_time.isoformat() if planned_time else None,
                    'status': status_info['status'],
                    'checkin_time': status_info['checkin_time'],
                    'rule_source': 'community',
                    'is_editable': False,
                    'community_name': rule.community.name if rule.community else None,
                    'time_slot_type': rule.time_slot_type
                }

                today_plan.append(plan_item)

            # 按计划时间排序
            today_plan.sort(key=lambda x: x['planned_time'] or '')

            # 返回与checkin_rule_service.py相同格式的数据结构
            result = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'total_items': len(today_plan),
                'completed_items': len([item for item in today_plan if item.get('status') == 'completed']),
                'pending_items': len([item for item in today_plan if item.get('status') != 'completed']),
                'items': today_plan
            }

            logger.info(f"获取用户今日计划成功: 用户ID={user_id}, 事项数量={len(today_plan)}")
            return result

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
                rule = UserCheckinRuleService.query_rule_by_id(rule_id)
                if not rule or rule.user_id != user_id:  # 更新字段名
                    raise ValueError('个人规则不存在或无权限')

                rule_dict = rule.to_dict()
                rule_dict['rule_source'] = 'personal'
                rule_dict['is_editable'] = True

            elif rule_source == 'community':
                # 获取社区规则
                rule = CommunityRuleQueryHelper.get_rule_detail(rule_id)

                # 检查用户是否有权限查看此规则
                user = db.session.get(User, user_id)
                if not user or user.community_id != rule['community_id']:
                    raise ValueError('社区规则不存在或无权限')

                # 使用 SQLAlchemy 2.0 的 select() 语句
                # 检查规则是否对用户生效
                stmt = select(UserCommunityRule).where(
                    UserCommunityRule.user_id == user_id,
                    UserCommunityRule.community_rule_id == rule_id,
                    UserCommunityRule.is_active == True
                )
                mapping = db.session.execute(stmt).scalar_one_or_none()

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

        """
        获取用户规则统计信息

        Args:
            user_id: 用户ID

        Returns:
            dict: 统计信息
        """
        try:
            # 获取个人规则数量
            personal_rules = UserCheckinRuleService.query_rules_by_user_id(user_id)
            personal_count = len(personal_rules)

            # 获取社区规则数量
            community_rules = CommunityRuleQueryHelper.get_user_community_rules(user_id)
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

    # ==================== 从 CheckinRuleService 迁移的方法 ====================

    @staticmethod
    def query_rules_by_user_id(user_id):
        """
        根据用户ID查询打卡规则列表（排除已删除）
        :param user_id: 用户ID
        :return: 打卡规则列表
        """
        try:
            stmt = select(CheckinRule).where(
                CheckinRule.user_id == user_id,
                CheckinRule.status == 1
            )
            rules = db.session.execute(stmt).scalars().all()
            return rules or []
        except Exception as e:
            logger.error(f"查询用户打卡规则失败: {str(e)}")
            return []

    @staticmethod
    def query_rule_by_id(rule_id):
        """
        根据规则ID查询打卡规则
        :param rule_id: 规则ID
        :return: 打卡规则实体（排除已删除的规则）
        """
        try:
            stmt = select(CheckinRule).where(
                CheckinRule.rule_id == rule_id,
                CheckinRule.status != 2  # 排除已删除的规则
            )
            rule = db.session.execute(stmt).scalar_one_or_none()
            return rule
        except Exception as e:
            logger.error(f"查询打卡规则失败: {str(e)}")
            return None

    @staticmethod
    def get_today_checkin_plan_personal(user_id):
        """
        获取用户今日打卡计划（仅个人规则）
        :param user_id: 用户ID
        :return: 今日打卡事项列表
        """
        try:
            # 获取用户的打卡规则
            checkin_rules = UserCheckinRuleService.query_rules_by_user_id(user_id)

            # 生成今天的打卡计划
            today = date.today()
            checkin_items = []

            for rule in checkin_rules:
                # 判断今天是否需要打卡
                if not UserCheckinRuleService._should_checkin_today(rule, today):
                    continue

                # 查询今天该规则的打卡记录
                today_records = UserCheckinRuleService._query_today_records(rule.rule_id, today)

                # 计算计划打卡时间
                planned_time = UserCheckinRuleService._calculate_planned_time(rule, today)

                # 确定打卡状态
                status_info = UserCheckinRuleService._determine_checkin_status(today_records)

                checkin_items.append({
                    'rule_id': rule.rule_id,
                    'record_id': status_info['record_id'],
                    'rule_name': rule.rule_name,
                    'icon_url': rule.icon_url,
                    'planned_time': planned_time.strftime('%H:%M:%S'),
                    'status': status_info['status'],
                    'checkin_time': status_info['checkin_time'],
                    'time_slot_type': rule.time_slot_type
                })

            return {
                'date': today.strftime('%Y-%m-%d'),
                'checkin_items': checkin_items
            }

        except Exception as e:
            logger.error(f"获取今日打卡计划失败: {str(e)}")
            raise

    @staticmethod
    def _get_rule_attr(rule, attr_name):
        """
        通用方法：获取规则属性，支持CheckinRule、CommunityCheckinRule、字典和列表格式
        """
        if isinstance(rule, list):
            logger.warning(f"尝试从列表对象获取属性 '{attr_name}'，但列表对象不支持属性访问")
            return None
        elif isinstance(rule, dict):
            if attr_name == 'rule_id':
                return rule.get('community_rule_id')
            return rule.get(attr_name)

        if isinstance(rule, CommunityCheckinRule):
            if attr_name == 'rule_id':
                return rule.community_rule_id
        return getattr(rule, attr_name, None)

    @staticmethod
    def _should_checkin_today(rule, today):
        """
        判断今天是否需要打卡
        :param rule: 打卡规则（CheckinRule或CommunityCheckinRule）
        :param today: 今天的日期
        :return: Boolean
        """
        frequency_type = UserCheckinRuleService._get_rule_attr(rule, 'frequency_type')
        week_days = UserCheckinRuleService._get_rule_attr(rule, 'week_days')
        custom_start_date = UserCheckinRuleService._get_rule_attr(rule, 'custom_start_date')
        custom_end_date = UserCheckinRuleService._get_rule_attr(rule, 'custom_end_date')

        if frequency_type == 1:  # 每周
            today_weekday = today.weekday()
            return bool(week_days & (1 << today_weekday))
        elif frequency_type == 2:  # 工作日
            return today.weekday() < 5
        elif frequency_type == 3:  # 自定义日期范围
            if custom_start_date and custom_end_date:
                return custom_start_date <= today <= custom_end_date
            return False
        else:  # 每天
            return True

    @staticmethod
    def _query_today_records(rule_id, today, rule_source='personal'):
        """
        查询今天该规则的打卡记录
        :param rule_id: 规则ID
        :param today: 今天的日期
        :param rule_source: 规则来源（personal/community）
        :return: 打卡记录列表
        """
        try:
            stmt = select(CheckinRecord).options(
                noload(CheckinRecord.user),
                noload(CheckinRecord.solo_user),
                noload(CheckinRecord.rule)
            ).where(
                func.date(CheckinRecord.planned_time) == today
            )

            if rule_source == 'community':
                stmt = stmt.where(CheckinRecord.community_rule_id == rule_id)
            else:
                stmt = stmt.where(CheckinRecord.rule_id == rule_id)

            records = db.session.execute(stmt).scalars().all()
            return records
        except Exception as e:
            logger.error(f"查询今日打卡记录失败: {str(e)}")
            return []

    @staticmethod
    def _calculate_planned_time(rule, today):
        """
        计算计划打卡时间
        :param rule: 打卡规则（CheckinRule或CommunityCheckinRule）
        :param today: 今天的日期
        :return: datetime 对象
        """
        time_slot_type = UserCheckinRuleService._get_rule_attr(rule, 'time_slot_type')
        custom_time = UserCheckinRuleService._get_rule_attr(rule, 'custom_time')

        if time_slot_type == 5:  # 全天有效
            return datetime.combine(today, time(0, 0))
        elif time_slot_type == 4 and custom_time:  # 自定义时间
            if isinstance(custom_time, str):
                try:
                    custom_time = parse_time_only(custom_time)
                except ValueError as e:
                    logger.warning(f"解析自定义时间失败: {custom_time}, 错误: {e}")
                    return datetime.combine(today, time(20, 0))

            if not isinstance(custom_time, time):
                logger.warning(f"custom_time不是有效的datetime.time对象: {custom_time}, 类型: {type(custom_time)}")
                return datetime.combine(today, time(20, 0))

            return datetime.combine(today, custom_time)
        elif time_slot_type == 1:  # 上午
            return datetime.combine(today, time(9, 0))
        elif time_slot_type == 2:  # 下午
            return datetime.combine(today, time(14, 0))
        else:  # 晚上
            return datetime.combine(today, time(20, 0))

    @staticmethod
    def _determine_checkin_status(today_records):
        """
        确定打卡状态
        :param today_records: 今日打卡记录列表
        :return: 状态信息字典
        """
        status_info = {
            'status': 'pending',
            'checkin_time': None,
            'record_id': None
        }

        for record in today_records:
            if record.status == 1:  # 已打卡
                status_info['status'] = 'checked'
                status_info['checkin_time'] = record.checkin_time.strftime('%H:%M:%S') if record.checkin_time else None
                status_info['record_id'] = record.record_id
                break
            elif record.status == 2:  # 已撤销
                status_info['status'] = 'unchecked'
                status_info['checkin_time'] = None
                status_info['record_id'] = record.record_id
                break

        return status_info