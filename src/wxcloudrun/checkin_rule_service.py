"""
打卡规则服务模块
处理打卡规则相关的核心业务逻辑
"""

import logging
from datetime import datetime, date, time
from sqlalchemy.exc import OperationalError
from .dao import get_db
from database.models import CheckinRule, CheckinRecord

logger = logging.getLogger('CheckinRuleService')


class CheckinRuleService:
    """打卡规则服务类"""

    @staticmethod
    def query_rules_by_user_id(user_id, session=None):
        """
        根据用户ID查询打卡规则列表（排除已删除）
        :param user_id: 用户ID
        :param session: 可选的数据库会话，如果为None则创建新会话
        :return: 打卡规则列表
        """
        try:
            if session is None:
                with get_db().get_session() as session:
                    rules = session.query(CheckinRule).filter(
                        CheckinRule.solo_user_id == user_id,
                        CheckinRule.status != 2  # 排除已删除的规则
                    ).all()
                    # 确保对象在会话关闭后仍可访问
                    for rule in rules:
                        session.expunge(rule)
                    return rules
            else:
                rules = session.query(CheckinRule).filter(
                    CheckinRule.solo_user_id == user_id,
                    CheckinRule.status != 2  # 排除已删除的规则
                ).all()
                return rules
        except OperationalError as e:
            logger.error(f"查询用户打卡规则失败: {str(e)}")
            return []

    @staticmethod
    def query_rule_by_id(rule_id, session=None):
        """
        根据规则ID查询打卡规则
        :param rule_id: 规则ID
        :param session: 可选的数据库会话，如果为None则创建新会话
        :return: 打卡规则实体
        """
        try:
            if session is None:
                with get_db().get_session() as session:
                    rule = session.query(CheckinRule).get(rule_id)
                    if rule:
                        session.expunge(rule)
                    return rule
            else:
                rule = session.query(CheckinRule).get(rule_id)
                return rule
        except OperationalError as e:
            logger.error(f"查询打卡规则失败: {str(e)}")
            return None

    @staticmethod
    def create_rule(rule_data, user_id, session=None):
        """
        创建打卡规则
        :param rule_data: 规则数据字典
        :param user_id: 用户ID
        :param session: 可选的数据库会话，如果为None则创建新会话
        :return: 创建的规则实体
        :raises ValueError: 当参数验证失败时
        """
        # 业务验证
        if not rule_data.get('rule_name'):
            raise ValueError('规则名称不能为空')

        frequency_type = rule_data.get('frequency_type', 0)

        # 验证自定义频率的日期范围
        if int(frequency_type) == 3:  # 自定义频率
            start_date = rule_data.get('custom_start_date')
            end_date = rule_data.get('custom_end_date')
            if not start_date or not end_date:
                raise ValueError('自定义频率必须提供起止日期')
            if end_date < start_date:
                raise ValueError('结束日期不能早于开始日期')

        try:
            # 创建规则实体
            new_rule = CheckinRule(
                solo_user_id=user_id,
                rule_name=rule_data['rule_name'],
                icon_url=rule_data.get('icon_url', ''),
                frequency_type=frequency_type,
                time_slot_type=rule_data.get('time_slot_type', 4),
                custom_time=rule_data.get('custom_time'),
                week_days=rule_data.get('week_days', 127),
                custom_start_date=rule_data.get('custom_start_date'),
                custom_end_date=rule_data.get('custom_end_date'),
                status=rule_data.get('status', 1)
            )

            if session is None:
                with get_db().get_session() as session:
                    session.add(new_rule)
                    session.commit()
                    session.refresh(new_rule)
                    session.expunge(new_rule)

                logger.info(f"创建打卡规则成功: 用户ID={user_id}, 规则ID={new_rule.rule_id}")
                return new_rule
            else:
                session.add(new_rule)
                # 注意：当使用外部传入的session时，由调用者负责提交事务
                # 这里只刷新对象，不提交
                session.flush()
                session.refresh(new_rule)
                logger.info(f"创建打卡规则成功（使用外部会话）: 用户ID={user_id}, 规则ID={new_rule.rule_id}")
                return new_rule

        except Exception as e:
            logger.error(f"创建打卡规则失败: {str(e)}")
            raise

    @staticmethod
    def update_rule(rule_id, rule_data, user_id, session=None):
        """
        更新打卡规则
        :param rule_id: 规则ID
        :param rule_data: 更新的规则数据字典
        :param user_id: 用户ID（用于权限验证）
        :param session: 可选的数据库会话，如果为None则创建新会话
        :return: 更新后的规则实体
        :raises ValueError: 当规则不存在或无权限时
        """
        try:
            if session is None:
                with get_db().get_session() as session:
                    rule = session.query(CheckinRule).get(rule_id)

                    if not rule:
                        raise ValueError('打卡规则不存在')

                    # 权限验证
                    if rule.solo_user_id != user_id:
                        raise ValueError('无权限修改此打卡规则')

                    # 更新字段
                    if 'rule_name' in rule_data:
                        rule.rule_name = rule_data['rule_name']
                    if 'icon_url' in rule_data:
                        rule.icon_url = rule_data['icon_url']
                    if 'frequency_type' in rule_data:
                        rule.frequency_type = rule_data['frequency_type']
                    if 'time_slot_type' in rule_data:
                        rule.time_slot_type = rule_data['time_slot_type']
                    if 'custom_time' in rule_data:
                        rule.custom_time = rule_data['custom_time']
                    if 'week_days' in rule_data:
                        rule.week_days = rule_data['week_days']
                    if 'custom_start_date' in rule_data:
                        rule.custom_start_date = rule_data['custom_start_date']
                    if 'custom_end_date' in rule_data:
                        rule.custom_end_date = rule_data['custom_end_date']
                    if 'status' in rule_data:
                        rule.status = rule_data['status']

                    rule.updated_at = datetime.now()

                    # 验证自定义频率的日期范围
                    if rule.frequency_type == 3:
                        if not rule.custom_start_date or not rule.custom_end_date:
                            raise ValueError('自定义频率必须提供起止日期')
                        if rule.custom_end_date < rule.custom_start_date:
                            raise ValueError('结束日期不能早于开始日期')

                    session.flush()
                    session.commit()
                    session.refresh(rule)
                    session.expunge(rule)

                    logger.info(f"更新打卡规则成功: 规则ID={rule_id}")
                    return rule
            else:
                rule = session.query(CheckinRule).get(rule_id)

                if not rule:
                    raise ValueError('打卡规则不存在')

                # 权限验证
                if rule.solo_user_id != user_id:
                    raise ValueError('无权限修改此打卡规则')

                # 更新字段
                if 'rule_name' in rule_data:
                    rule.rule_name = rule_data['rule_name']
                if 'icon_url' in rule_data:
                    rule.icon_url = rule_data['icon_url']
                if 'frequency_type' in rule_data:
                    rule.frequency_type = rule_data['frequency_type']
                if 'time_slot_type' in rule_data:
                    rule.time_slot_type = rule_data['time_slot_type']
                if 'custom_time' in rule_data:
                    rule.custom_time = rule_data['custom_time']
                if 'week_days' in rule_data:
                    rule.week_days = rule_data['week_days']
                if 'custom_start_date' in rule_data:
                    rule.custom_start_date = rule_data['custom_start_date']
                if 'custom_end_date' in rule_data:
                    rule.custom_end_date = rule_data['custom_end_date']
                if 'status' in rule_data:
                    rule.status = rule_data['status']

                rule.updated_at = datetime.now()

                # 验证自定义频率的日期范围
                if rule.frequency_type == 3:
                    if not rule.custom_start_date or not rule.custom_end_date:
                        raise ValueError('自定义频率必须提供起止日期')
                    if rule.custom_end_date < rule.custom_start_date:
                        raise ValueError('结束日期不能早于开始日期')

                # 注意：当使用外部传入的session时，由调用者负责提交事务
                # 这里只刷新对象，不提交
                session.flush()
                session.refresh(rule)

                logger.info(f"更新打卡规则成功（使用外部会话）: 规则ID={rule_id}")
                return rule

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"更新打卡规则失败: {str(e)}")
            raise

    @staticmethod
    def delete_rule(rule_id, user_id, session=None):
        """
        软删除打卡规则
        :param rule_id: 规则ID
        :param user_id: 用户ID（用于权限验证）
        :param session: 可选的数据库会话，如果为None则创建新会话
        :return: True 删除成功
        :raises ValueError: 当规则不存在或无权限时
        """
        try:
            if session is None:
                with get_db().get_session() as session:
                    rule = session.query(CheckinRule).get(rule_id)

                    if not rule:
                        raise ValueError(f"没有找到 id 为 {rule_id} 的打卡规则")

                    # 权限验证
                    if rule.solo_user_id != user_id:
                        raise ValueError('无权限删除此打卡规则')

                    # 软删除
                    rule.status = 2  # 已删除
                    rule.deleted_at = datetime.now()

                    session.commit()

                    logger.info(f"删除打卡规则成功: 规则ID={rule_id}")
                    return True
            else:
                rule = session.query(CheckinRule).get(rule_id)

                if not rule:
                    raise ValueError(f"没有找到 id 为 {rule_id} 的打卡规则")

                # 权限验证
                if rule.solo_user_id != user_id:
                    raise ValueError('无权限删除此打卡规则')

                # 软删除
                rule.status = 2  # 已删除
                rule.deleted_at = datetime.now()

                # 注意：当使用外部传入的session时，由调用者负责提交事务
                # 这里只标记删除，不提交

                logger.info(f"删除打卡规则成功（使用外部会话）: 规则ID={rule_id}")
                return True

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"删除打卡规则失败: {str(e)}")
            raise

    @staticmethod
    def get_today_checkin_plan(user_id, session=None):
        """
        获取用户今日打卡计划
        :param user_id: 用户ID
        :param session: 可选的数据库会话，如果为None则创建新会话
        :return: 今日打卡事项列表
        """
        try:
            # 获取用户的打卡规则
            checkin_rules = CheckinRuleService.query_rules_by_user_id(user_id, session)

            # 生成今天的打卡计划
            today = date.today()
            checkin_items = []

            for rule in checkin_rules:
                # 判断今天是否需要打卡
                if not CheckinRuleService._should_checkin_today(rule, today):
                    continue

                # 查询今天该规则的打卡记录
                today_records = CheckinRuleService._query_today_records(rule.rule_id, today, session)

                # 计算计划打卡时间
                planned_time = CheckinRuleService._calculate_planned_time(rule, today)

                # 确定打卡状态
                status_info = CheckinRuleService._determine_checkin_status(today_records)

                checkin_items.append({
                    'rule_id': rule.rule_id,
                    'record_id': status_info['record_id'],
                    'rule_name': rule.rule_name,
                    'icon_url': rule.icon_url,
                    'planned_time': planned_time.strftime('%H:%M:%S'),
                    'status': status_info['status'],
                    'checkin_time': status_info['checkin_time']
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
        通用方法：获取规则属性，支持CheckinRule、CommunityCheckinRule和字典格式

        Args:
            rule: 规则对象（CheckinRule、CommunityCheckinRule或字典）
            attr_name: 属性名

        Returns:
            属性值
        """
        # 处理字典格式的规则数据
        if isinstance(rule, dict):
            # 字典格式直接返回键值
            if attr_name == 'rule_id':
                # 社区规则字典中使用community_rule_id作为rule_id
                return rule.get('community_rule_id')
            return rule.get(attr_name)
        
        # 处理CommunityCheckinRule对象
        from database.models import CommunityCheckinRule
        if isinstance(rule, CommunityCheckinRule):
            # CommunityCheckinRule使用community_rule_id而不是rule_id
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
        frequency_type = CheckinRuleService._get_rule_attr(rule, 'frequency_type')
        week_days = CheckinRuleService._get_rule_attr(rule, 'week_days')
        custom_start_date = CheckinRuleService._get_rule_attr(rule, 'custom_start_date')
        custom_end_date = CheckinRuleService._get_rule_attr(rule, 'custom_end_date')

        if frequency_type == 1:  # 每周
            today_weekday = today.weekday()  # 0是周一，6是周日
            return bool(week_days & (1 << today_weekday))
        elif frequency_type == 2:  # 工作日
            return today.weekday() < 5  # 周一到周五
        elif frequency_type == 3:  # 自定义日期范围
            if custom_start_date and custom_end_date:
                return custom_start_date <= today <= custom_end_date
            return False
        else:  # 每天 (frequency_type == 0)
            return True

    @staticmethod
    def _query_today_records(rule_id, today, session=None, rule_source='personal'):
        """
        查询今天该规则的打卡记录
        :param rule_id: 规则ID
        :param today: 今天的日期
        :param session: 可选的数据库会话，如果为None则创建新会话
        :param rule_source: 规则来源（personal/community）
        :return: 打卡记录列表
        """
        try:
            from sqlalchemy import func
            if session is None:
                with get_db().get_session() as session:
                    query = session.query(CheckinRecord).filter(
                        func.date(CheckinRecord.planned_time) == today
                    )

                    # 根据规则来源过滤
                    if rule_source == 'community':
                        # 社区规则的打卡记录使用community_rule_id字段
                        query = query.filter(CheckinRecord.community_rule_id == rule_id)
                    else:
                        # 个人规则的打卡记录使用rule_id字段
                        query = query.filter(CheckinRecord.rule_id == rule_id)

                    records = query.all()
                    for record in records:
                        session.expunge(record)
                    return records
            else:
                query = session.query(CheckinRecord).filter(
                    func.date(CheckinRecord.planned_time) == today
                )

                if rule_source == 'community':
                    query = query.filter(CheckinRecord.community_rule_id == rule_id)
                else:
                    query = query.filter(CheckinRecord.rule_id == rule_id)

                return query.all()
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
        time_slot_type = CheckinRuleService._get_rule_attr(rule, 'time_slot_type')
        custom_time = CheckinRuleService._get_rule_attr(rule, 'custom_time')

        if time_slot_type == 4 and custom_time:  # 自定义时间
            # 确保custom_time是time对象，而不是字符串
            if isinstance(custom_time, str):
                from wxcloudrun.utils.timeutil import parse_time_only
                try:
                    custom_time = parse_time_only(custom_time)
                except ValueError as e:
                    logger.warning(f"解析自定义时间失败: {custom_time}, 错误: {e}")
                    # 如果解析失败，使用默认时间
                    return datetime.combine(today, time(20, 0))
            
            # 再次检查类型，确保是time对象
            if not hasattr(custom_time, 'hour'):  # 不是time对象
                logger.warning(f"custom_time不是有效的时间对象: {custom_time}, 类型: {type(custom_time)}")
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
            'status': 'unchecked',
            'checkin_time': None,
            'record_id': None
        }

        for record in today_records:
            if record.status == 1:  # 已打卡
                status_info['status'] = 'checked'
                status_info['checkin_time'] = record.checkin_time.strftime(
                    '%H:%M:%S') if record.checkin_time else None
                status_info['record_id'] = record.record_id
                break
            elif record.status == 2:  # 已撤销
                status_info['status'] = 'unchecked'
                status_info['checkin_time'] = None
                status_info['record_id'] = record.record_id
                break

        return status_info
