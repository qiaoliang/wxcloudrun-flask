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
    def query_rules_by_user_id(user_id):
        """
        根据用户ID查询打卡规则列表（排除已删除）
        :param user_id: 用户ID
        :return: 打卡规则列表
        """
        try:
            with get_db().get_session() as session:
                rules = session.query(CheckinRule).filter(
                    CheckinRule.solo_user_id == user_id,
                    CheckinRule.status != 2  # 排除已删除的规则
                ).all()
                # 确保对象在会话关闭后仍可访问
                for rule in rules:
                    session.expunge(rule)
                return rules
        except OperationalError as e:
            logger.error(f"查询用户打卡规则失败: {str(e)}")
            return []

    @staticmethod
    def query_rule_by_id(rule_id):
        """
        根据规则ID查询打卡规则
        :param rule_id: 规则ID
        :return: 打卡规则实体
        """
        try:
            with get_db().get_session() as session:
                rule = session.query(CheckinRule).get(rule_id)
                if rule:
                    session.expunge(rule)
                return rule
        except OperationalError as e:
            logger.error(f"查询打卡规则失败: {str(e)}")
            return None

    @staticmethod
    def create_rule(rule_data, user_id):
        """
        创建打卡规则
        :param rule_data: 规则数据字典
        :param user_id: 用户ID
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

            with get_db().get_session() as session:
                session.add(new_rule)
                session.commit()
                session.refresh(new_rule)
                session.expunge(new_rule)
                
            logger.info(f"创建打卡规则成功: 用户ID={user_id}, 规则ID={new_rule.rule_id}")
            return new_rule
            
        except Exception as e:
            logger.error(f"创建打卡规则失败: {str(e)}")
            raise

    @staticmethod
    def update_rule(rule_id, rule_data, user_id):
        """
        更新打卡规则
        :param rule_id: 规则ID
        :param rule_data: 更新的规则数据字典
        :param user_id: 用户ID（用于权限验证）
        :return: 更新后的规则实体
        :raises ValueError: 当规则不存在或无权限时
        """
        try:
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
                
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"更新打卡规则失败: {str(e)}")
            raise

    @staticmethod
    def delete_rule(rule_id, user_id):
        """
        软删除打卡规则
        :param rule_id: 规则ID
        :param user_id: 用户ID（用于权限验证）
        :return: True 删除成功
        :raises ValueError: 当规则不存在或无权限时
        """
        try:
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
                
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"删除打卡规则失败: {str(e)}")
            raise

    @staticmethod
    def get_today_checkin_plan(user_id):
        """
        获取用户今日打卡计划
        :param user_id: 用户ID
        :return: 今日打卡事项列表
        """
        try:
            # 获取用户的打卡规则
            checkin_rules = CheckinRuleService.query_rules_by_user_id(user_id)
            
            # 生成今天的打卡计划
            today = date.today()
            checkin_items = []
            
            for rule in checkin_rules:
                # 判断今天是否需要打卡
                if not CheckinRuleService._should_checkin_today(rule, today):
                    continue
                
                # 查询今天该规则的打卡记录
                today_records = CheckinRuleService._query_today_records(rule.rule_id, today)
                
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
    def _should_checkin_today(rule, today):
        """
        判断今天是否需要打卡
        :param rule: 打卡规则
        :param today: 今天的日期
        :return: Boolean
        """
        if rule.frequency_type == 1:  # 每周
            today_weekday = today.weekday()  # 0是周一，6是周日
            return bool(rule.week_days & (1 << today_weekday))
        elif rule.frequency_type == 2:  # 工作日
            return today.weekday() < 5  # 周一到周五
        elif rule.frequency_type == 3:  # 自定义日期范围
            if rule.custom_start_date and rule.custom_end_date:
                return rule.custom_start_date <= today <= rule.custom_end_date
            return False
        else:  # 每天 (frequency_type == 0)
            return True

    @staticmethod
    def _query_today_records(rule_id, today):
        """
        查询今天该规则的打卡记录
        :param rule_id: 规则ID
        :param today: 今天的日期
        :return: 打卡记录列表
        """
        try:
            from sqlalchemy import func
            with get_db().get_session() as session:
                records = session.query(CheckinRecord).filter(
                    CheckinRecord.rule_id == rule_id,
                    func.date(CheckinRecord.planned_time) == today
                ).all()
                for record in records:
                    session.expunge(record)
                return records
        except Exception as e:
            logger.error(f"查询今日打卡记录失败: {str(e)}")
            return []

    @staticmethod
    def _calculate_planned_time(rule, today):
        """
        计算计划打卡时间
        :param rule: 打卡规则
        :param today: 今天的日期
        :return: datetime 对象
        """
        if rule.time_slot_type == 4 and rule.custom_time:  # 自定义时间
            return datetime.combine(today, rule.custom_time)
        elif rule.time_slot_type == 1:  # 上午
            return datetime.combine(today, time(9, 0))
        elif rule.time_slot_type == 2:  # 下午
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
