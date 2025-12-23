"""
打卡记录服务模块
处理打卡记录相关的核心业务逻辑
"""

import logging
from datetime import datetime, date, time, timedelta
from sqlalchemy.exc import OperationalError
from sqlalchemy import func
from .checkin_rule_service import CheckinRuleService
from database.flask_models import CheckinRecord, SupervisionRuleRelation, db

logger = logging.getLogger('CheckinRecordService')


class CheckinRecordService:
    """打卡记录服务类"""

    # 撤销打卡的时间限制（分钟）
    CANCEL_TIME_LIMIT_MINUTES = 30

    @staticmethod
    def perform_checkin(rule_id, user_id, rule_source='personal'):
        """
        执行打卡操作
        :param rule_id: 规则ID
        :param user_id: 用户ID
        :param rule_source: 规则来源（personal/community）
        :return: 打卡记录信息字典
        :raises ValueError: 当规则不存在、无权限或今日已打卡时
        """
        if rule_source == 'community':
            # 验证社区规则是否存在且用户有权限
            from .community_checkin_rule_service import CommunityCheckinRuleService
            from .user_checkin_rule_service import UserCheckinRuleService

            rule = CommunityCheckinRuleService.get_rule_detail(rule_id)
            if not rule:
                raise ValueError('社区打卡规则不存在')

            # 检查用户是否有权限打卡此社区规则
            try:
                user_rule = UserCheckinRuleService.get_rule_by_id(rule_id, user_id, 'community')
            except ValueError:
                raise ValueError('无权限打卡此社区规则')

        else:
            # 验证个人规则是否存在且属于当前用户
            rule = CheckinRuleService.query_rule_by_id(rule_id)
            if not rule or rule.user_id != user_id:  # 更新字段名
                raise ValueError('打卡规则不存在或无权限')

        # 检查今天是否已有打卡记录
        today = date.today()
        existing_records = CheckinRecordService._query_records_by_rule_and_date(
            rule_id, today, rule_source)

        # 查找当天已有的打卡记录
        for record in existing_records:
            if record.status == 1:  # 已打卡
                raise ValueError('今日该事项已打卡，请勿重复打卡')

        # 记录打卡时间
        checkin_time = datetime.now()

        # 检查是否有未打卡状态的记录可以更新
        existing_unchecked = None
        for record in existing_records:
            if record.status == 0:  # 未打卡
                existing_unchecked = record
                break

        if existing_unchecked:
            # 更新已有记录
            record_id = CheckinRecordService._update_record_status(
                existing_unchecked.record_id, checkin_time, 1)
        else:
            # 创建新的打卡记录
            planned_time = CheckinRecordService._calculate_planned_time(rule, today)
            record_id = CheckinRecordService._create_record(
                rule_id, user_id, checkin_time, planned_time, status=1, rule_source=rule_source)

        logger.info(f"用户 {user_id} 打卡成功，规则ID: {rule_id}, 记录ID: {record_id}")

        return {
            'rule_id': rule_id,
            'record_id': record_id,
            'checkin_time': checkin_time.strftime('%Y-%m-%d %H:%M:%S'),
            'message': '打卡成功'
        }

    @staticmethod
    def mark_missed(rule_id, user_id):
        """
        标记当天规则为 missed（超过宽限期）
        :param rule_id: 规则ID
        :param user_id: 用户ID
        :return: 记录信息字典
        :raises ValueError: 当规则不存在、无权限或今日已打卡时
        """
        # 验证规则是否存在且属于当前用户
        rule = CheckinRuleService.query_rule_by_id(rule_id)
        if not rule or rule.user_id != user_id:  # 更新字段名
            raise ValueError('打卡规则不存在或无权限')

        # 检查今天是否已打卡
        today = date.today()
        records = CheckinRecordService._query_records_by_rule_and_date(rule_id, today)

        for record in records:
            if record.status == 1:  # 已打卡
                raise ValueError('今日该事项已打卡，无需标记miss')

        # 创建 missed 记录
        planned_time = CheckinRecordService._calculate_planned_time(rule, today)
        record_id = CheckinRecordService._create_record(
            rule_id, user_id, None, planned_time, status=0)

        logger.info(f"用户 {user_id} 标记miss成功，规则ID: {rule_id}, 记录ID: {record_id}")

        return {
            'record_id': record_id,
            'message': '已标记为miss'
        }

    @staticmethod
    def cancel_checkin(record_id, user_id):
        """
        撤销打卡操作（仅限30分钟内）
        :param record_id: 记录ID
        :param user_id: 用户ID
        :return: 撤销信息字典
        :raises ValueError: 当记录不存在、无权限或超过撤销时限时
        """
        # 查询打卡记录
        record = CheckinRecordService.query_record_by_id(record_id)
        if not record:
            raise ValueError('打卡记录不存在')

        # 权限验证
        if record.user_id != user_id:  # 更新字段名
            raise ValueError('无权限撤销此打卡记录')

        # 检查打卡时间是否在30分钟内
        if record.checkin_time:
            time_diff = datetime.now() - record.checkin_time
            if time_diff.total_seconds() > CheckinRecordService.CANCEL_TIME_LIMIT_MINUTES * 60:
                raise ValueError(f'只能撤销{CheckinRecordService.CANCEL_TIME_LIMIT_MINUTES}分钟内的打卡记录')

        # 更新记录状态为已撤销
        CheckinRecordService._update_record_status(record_id, None, 2)

        logger.info(f"用户 {user_id} 撤销打卡成功，记录ID: {record_id}")

        return {
            'record_id': record_id,
            'message': '撤销打卡成功'
        }

    @staticmethod
    def get_checkin_history(user_id, start_date, end_date):
        """
        获取打卡历史记录
        :param user_id: 用户ID
        :param start_date: 开始日期
        :param end_date: 结束日期
        :return: 历史记录字典
        """
        try:
            # 获取打卡记录
            records = CheckinRecordService._query_records_by_user_and_date_range(
                user_id, start_date, end_date)

            # 转换为响应格式
            history_data = []
            for record in records:
                history_data.append({
                    'record_id': record.record_id,
                    'rule_id': record.rule_id,
                    'rule_name': record.rule.rule_name,
                    'icon_url': record.rule.icon_url,
                    'planned_time': record.planned_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'checkin_time': record.checkin_time.strftime('%Y-%m-%d %H:%M:%S') if record.checkin_time else None,
                    'status': record.status_name,
                    'created_at': record.created_at.strftime('%Y-%m-%d %H:%M:%S')
                })

            logger.info(f"获取打卡历史成功，用户ID: {user_id}, 记录数量: {len(history_data)}")

            return {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'history': history_data
            }

        except Exception as e:
            logger.error(f"获取打卡历史失败: {str(e)}")
            raise

    @staticmethod
    def get_supervised_records(supervisor_user_id, start_date, end_date, session=None):
        """
        获取监护人可查看的被监护人打卡记录
        :param supervisor_user_id: 监护人用户ID
        :param start_date: 开始日期
        :param end_date: 结束日期
        :param session: 数据库会话，如果为None则创建新会话
        :return: 打卡记录列表
        """
        try:
            # 如果session为None，使用Flask-SQLAlchemy的session
            if session is None:
                # 获取监督关系
                relations = db.session.query(SupervisionRuleRelation).filter(
                    SupervisionRuleRelation.supervisor_user_id == supervisor_user_id,
                    SupervisionRuleRelation.status == 2  # 已同意
                ).all()

                if not relations:
                    return []

                # 分离可以监督所有规则的用户和特定规则的关系
                all_rules_users = set()
                specific_rules = []

                for relation in relations:
                    if relation.rule_id is None:
                        all_rules_users.add(relation.solo_user_id)
                    else:
                        specific_rules.append({
                            'user_id': relation.solo_user_id,
                            'rule_id': relation.rule_id
                        })

                # 查询打卡记录
                records = []

                # 查询可以监督所有规则的用户的记录
                if all_rules_users:
                    all_rules_records = db.session.query(CheckinRecord).filter(
                        CheckinRecord.user_id.in_(all_rules_users),
                        CheckinRecord.planned_time >= start_date,
                        CheckinRecord.planned_time <= end_date
                    ).all()
                    records.extend(all_rules_records)

                # 查询特定规则的记录
                for spec in specific_rules:
                    spec_records = db.session.query(CheckinRecord).filter(
                        CheckinRecord.user_id == spec['user_id'],
                        CheckinRecord.rule_id == spec['rule_id'],
                        CheckinRecord.planned_time >= start_date,
                        CheckinRecord.planned_time <= end_date
                    ).all()
                    records.extend(spec_records)

                # 去重并排序
                unique_records = list({r.record_id: r for r in records}.values())
                unique_records.sort(key=lambda x: x.planned_time, reverse=True)

                # Flask-SQLAlchemy 会自动处理对象状态，不需要 expunge

                logger.info(f"获取监督记录成功，监护人ID: {supervisor_user_id}, 记录数量: {len(unique_records)}")
                return unique_records
            else:
                # 使用传入的session
                # 获取监督关系
                relations = session.query(SupervisionRuleRelation).filter(
                    SupervisionRuleRelation.supervisor_user_id == supervisor_user_id,
                    SupervisionRuleRelation.status == 2  # 已同意
                ).all()

                if not relations:
                    return []

                # 分离可以监督所有规则的用户和特定规则的关系
                all_rules_users = set()
                specific_rules = []

                for relation in relations:
                    if relation.rule_id is None:
                        all_rules_users.add(relation.solo_user_id)
                    else:
                        specific_rules.append({
                            'user_id': relation.solo_user_id,
                            'rule_id': relation.rule_id
                        })

                # 查询打卡记录
                records = []

                # 查询可以监督所有规则的用户的记录
                if all_rules_users:
                    all_rules_records = session.query(CheckinRecord).filter(
                        CheckinRecord.user_id.in_(all_rules_users),
                        CheckinRecord.planned_time >= start_date,
                        CheckinRecord.planned_time <= end_date
                    ).all()
                    records.extend(all_rules_records)

                # 查询特定规则的记录
                for spec in specific_rules:
                    spec_records = session.query(CheckinRecord).filter(
                        CheckinRecord.user_id == spec['user_id'],
                        CheckinRecord.rule_id == spec['rule_id'],
                        CheckinRecord.planned_time >= start_date,
                        CheckinRecord.planned_time <= end_date
                    ).all()
                    records.extend(spec_records)

                # 去重并排序
                unique_records = list({r.record_id: r for r in records}.values())
                unique_records.sort(key=lambda x: x.planned_time, reverse=True)

                # 注意：使用外部传入的session时，不进行expunge操作
                logger.info(f"获取监督记录成功，监护人ID: {supervisor_user_id}, 记录数量: {len(unique_records)}")
                return unique_records

        except Exception as e:
            logger.error(f"获取监督记录失败: {str(e)}")
            return []

    # ========== 私有辅助方法 ==========

    @staticmethod
    def query_record_by_id(record_id, session=None):
        """
        根据记录ID查询打卡记录
        :param record_id: 记录ID
        :param session: 数据库会话，如果为None则创建新会话
        :return: 打卡记录实体
        """
        try:
            # 如果session为None，使用Flask-SQLAlchemy的session
            if session is None:
                record = db.session.query(CheckinRecord).get(record_id)
                return record
            else:
                # 使用传入的session
                record = session.query(CheckinRecord).get(record_id)
                # 注意：使用外部传入的session时，不进行expunge操作
                return record
        except OperationalError as e:
            logger.error(f"查询打卡记录失败: {str(e)}")
            return None

    @staticmethod
    def _query_records_by_rule_and_date(rule_id, checkin_date, rule_source='personal', session=None):
        """
        根据规则ID和日期查询打卡记录
        :param rule_id: 规则ID
        :param checkin_date: 打卡日期
        :param rule_source: 规则来源（personal/community）
        :param session: 数据库会话，如果为None则创建新会话
        :return: 打卡记录列表
        """
        try:
            # 如果session为None，使用Flask-SQLAlchemy的session
            if session is None:
                if rule_source == 'community':
                    # 查询社区规则打卡记录
                    records = db.session.query(CheckinRecord).filter(
                        CheckinRecord.community_rule_id == rule_id,
                        func.date(CheckinRecord.planned_time) == checkin_date
                    ).all()
                else:
                    # 查询个人规则打卡记录
                    records = db.session.query(CheckinRecord).filter(
                        CheckinRecord.rule_id == rule_id,
                        func.date(CheckinRecord.planned_time) == checkin_date
                    ).all()
                return records
            else:
                # 使用传入的session
                if rule_source == 'community':
                    # 查询社区规则打卡记录
                    records = session.query(CheckinRecord).filter(
                        CheckinRecord.community_rule_id == rule_id,
                        func.date(CheckinRecord.planned_time) == checkin_date
                    ).all()
                else:
                    # 查询个人规则打卡记录
                    records = session.query(CheckinRecord).filter(
                        CheckinRecord.rule_id == rule_id,
                        func.date(CheckinRecord.planned_time) == checkin_date
                    ).all()
                # 注意：使用外部传入的session时，不进行expunge操作
                return records
        except OperationalError as e:
            logger.error(f"查询打卡记录失败: {str(e)}")
            return []

    @staticmethod
    def _query_records_by_user_and_date_range(user_id, start_date, end_date, session=None):
        """
        根据用户ID和日期范围查询打卡记录
        :param user_id: 用户ID
        :param start_date: 开始日期
        :param end_date: 结束日期
        :param session: 数据库会话，如果为None则创建新会话
        :return: 打卡记录列表
        """
        try:
            # 如果session为None，使用Flask-SQLAlchemy的session
            if session is None:
                records = db.session.query(CheckinRecord).filter(
                    CheckinRecord.user_id == user_id,
                    CheckinRecord.planned_time >= start_date,
                    CheckinRecord.planned_time <= end_date
                ).order_by(CheckinRecord.planned_time.desc()).all()
                return records
            else:
                # 使用传入的session
                records = session.query(CheckinRecord).filter(
                    CheckinRecord.user_id == user_id,
                    CheckinRecord.planned_time >= start_date,
                    CheckinRecord.planned_time <= end_date
                ).order_by(CheckinRecord.planned_time.desc()).all()
                # 注意：使用外部传入的session时，不进行expunge操作
                return records
        except OperationalError as e:
            logger.error(f"查询打卡记录失败: {str(e)}")
            return []

    @staticmethod
    def _calculate_planned_time(rule, target_date):
        """
        计算计划打卡时间
        :param rule: 打卡规则（对象或字典）
        :param target_date: 目标日期
        :return: datetime 对象
        """
        # 处理字典格式的规则（社区规则）
        if isinstance(rule, dict):
            time_slot_type = rule.get('time_slot_type')
            custom_time = rule.get('custom_time')
            # 社区规则的custom_time是ISO格式字符串，需要转换为time对象
            if custom_time and isinstance(custom_time, str):
                from wxcloudrun.utils.timeutil import parse_time_only
                try:
                    custom_time = parse_time_only(custom_time)
                except ValueError as e:
                    logger.warning(f"解析自定义时间失败: {custom_time}, 错误: {e}")
                    # 如果解析失败，使用默认时间
                    return datetime.combine(target_date, time(20, 0))
        else:
            # 处理对象格式的规则（个人规则）
            time_slot_type = rule.time_slot_type
            custom_time = rule.custom_time
            # 确保custom_time是time对象，而不是字符串
            if custom_time and isinstance(custom_time, str):
                from wxcloudrun.utils.timeutil import parse_time_only
                try:
                    custom_time = parse_time_only(custom_time)
                except ValueError as e:
                    logger.warning(f"解析自定义时间失败: {custom_time}, 错误: {e}")
                    # 如果解析失败，使用默认时间
                    return datetime.combine(target_date, time(20, 0))

        if time_slot_type == 4 and custom_time:  # 自定义时间
            # 再次检查类型，确保是time对象
            if not hasattr(custom_time, 'hour'):  # 不是time对象
                logger.warning(f"custom_time不是有效的时间对象: {custom_time}, 类型: {type(custom_time)}")
                return datetime.combine(target_date, time(20, 0))

            return datetime.combine(target_date, custom_time)
        elif time_slot_type == 1:  # 上午
            return datetime.combine(target_date, time(9, 0))
        elif time_slot_type == 2:  # 下午
            return datetime.combine(target_date, time(14, 0))
        else:  # 晚上
            return datetime.combine(target_date, time(20, 0))

    @staticmethod
    def _create_record(rule_id, user_id, checkin_time, planned_time, status, rule_source='personal', session=None):
        """
        创建打卡记录
        :param rule_id: 规则ID
        :param user_id: 用户ID
        :param checkin_time: 打卡时间（可为None）
        :param planned_time: 计划时间
        :param status: 状态（0-未打卡，1-已打卡）
        :param rule_source: 规则来源（personal/community）
        :param session: 数据库会话，如果为None则创建新会话
        :return: 记录ID
        """
        try:
            if rule_source == 'community':
                # 社区规则打卡记录
                new_record = CheckinRecord(
                    community_rule_id=rule_id,
                    solo_user_id=user_id,
                    checkin_time=checkin_time,
                    status=status,
                    planned_time=planned_time
                )
            else:
                # 个人规则打卡记录
                new_record = CheckinRecord(
                    rule_id=rule_id,
                    user_id=user_id,  # 更新字段名
                    checkin_time=checkin_time,
                    status=status,
                    planned_time=planned_time
                )

            # 如果session为None，使用Flask-SQLAlchemy的session
            if session is None:
                db.session.add(new_record)
                db.session.commit()
                db.session.refresh(new_record)
                record_id = new_record.record_id
                # Flask-SQLAlchemy 会自动处理对象状态，不需要 expunge

                return record_id
            else:
                # 使用传入的session
                session.add(new_record)
                # 注意：使用外部传入的session时，由调用者负责commit
                session.flush()  # 使用 flush 而不是 refresh，确保对象在session中
                record_id = new_record.record_id
                # 注意：使用外部传入的session时，不进行expunge操作
                return record_id

        except Exception as e:
            logger.error(f"创建打卡记录失败: {str(e)}")
            raise

    @staticmethod
    def _update_record_status(record_id, checkin_time, status, session=None):
        """
        更新打卡记录状态
        :param record_id: 记录ID
        :param checkin_time: 打卡时间（可为None）
        :param status: 状态
        :param session: 数据库会话，如果为None则创建新会话
        :return: 记录ID
        """
        try:
            # 如果session为None，使用Flask-SQLAlchemy的session
            if session is None:
                record = db.session.query(CheckinRecord).get(record_id)
                if not record:
                    raise ValueError('打卡记录不存在')

                record.checkin_time = checkin_time
                record.status = status
                record.updated_at = datetime.now()

                db.session.flush()
                db.session.commit()

                return record_id
            else:
                # 使用传入的session
                record = session.query(CheckinRecord).get(record_id)
                if not record:
                    raise ValueError('打卡记录不存在')

                record.checkin_time = checkin_time
                record.status = status
                record.updated_at = datetime.now()

                session.flush()
                # 注意：使用外部传入的session时，由调用者负责commit

                return record_id

        except Exception as e:
            logger.error(f"更新打卡记录失败: {str(e)}")
            raise
