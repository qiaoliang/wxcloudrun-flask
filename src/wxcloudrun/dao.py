import logging
from datetime import datetime, date
from sqlalchemy.exc import OperationalError
from sqlalchemy import and_, or_

from database import get_database
from database.models import Counters, User, CheckinRule, CheckinRecord

# 获取数据库实例
db = get_database()

# 初始化日志
logger = logging.getLogger('log')


def query_counterbyid(id):
    """
    根据ID查询Counter实体
    :param id: Counter的ID
    :return: Counter实体
    """
    try:
        with db.get_session() as session:
            result = session.query(Counters).filter(Counters.id == id).first()
            logger.info(f"query_counterbyid: 查询ID {id} 的结果 - {'找到计数器' if result else '未找到计数器'}")
            if result:
                logger.info(f"query_counterbyid: 计数器值为 {result.count}")
            return result
    except OperationalError as e:
        logger.error("query_counterbyid errorMsg= {} ".format(e))
        return None


def delete_counterbyid(id):
    """
    根据ID删除Counter实体
    :param id: Counter的ID
    """
    try:
        with db.get_session() as session:
            logger.info(f"delete_counterbyid: 准备删除ID为 {id} 的计数器")
            counter = session.query(Counters).get(id)
            if counter is None:
                logger.warning(f"delete_counterbyid: 未找到ID为 {id} 的计数器进行删除")
                return
            logger.info(f"delete_counterbyid: 找到计数器，值为 {counter.count}")
            session.delete(counter)
            session.commit()
            logger.info(f"delete_counterbyid: 成功删除ID为 {id} 的计数器")
    except OperationalError as e:
        logger.error("delete_counterbyid errorMsg= {} ".format(e))


def insert_counter(counter):
    """
    插入一个Counter实体
    :param counter: Counters实体
    """
    try:
        with db.get_session() as session:
            logger.info(f"insert_counter: 准备插入计数器，ID: {counter.id}, 值: {counter.count}")
            session.add(counter)
            session.commit()
            logger.info(f"insert_counter: 成功插入计数器，ID: {counter.id}, 值: {counter.count}")
    except OperationalError as e:
        logger.error("insert_counter errorMsg= {} ".format(e))


def update_counterbyid(counter):
    """
    根据ID更新counter的值
    :param counter实体
    """
    try:
        logger.info(f"update_counterbyid: 准备更新计数器，ID: {counter.id}, 新值: {counter.count}")
        existing_counter = query_counterbyid(counter.id)
        if existing_counter is None:
            logger.warning(f"update_counterbyid: 未找到ID为 {counter.id} 的计数器进行更新")
            return
        logger.info(f"update_counterbyid: 找到现有计数器，当前值: {existing_counter.count}")
        # 更新现有记录的值
        existing_counter.count = counter.count
        existing_counter.updated_at = counter.updated_at
        logger.info(f"update_counterbyid: 设置新值为 {existing_counter.count}")
        db.session.flush()
        logger.info("update_counterbyid: 执行session flush")
        db.session.commit()
        logger.info(f"update_counterbyid: 成功提交更新，ID: {counter.id}, 值: {existing_counter.count}")
    except OperationalError as e:
        logger.error("update_counterbyid errorMsg= {} ".format(e))


def query_user_by_openid(openid):
    """
    根据微信OpenID查询用户实体
    :param openid: 微信OpenID
    :return: User实体
    """
    try:
        with db.get_session() as session:
            return session.query(User).filter(User.wechat_openid == openid).first()
    except OperationalError as e:
        logger.info("query_user_by_openid errorMsg= {} ".format(e))
        return None


def query_user_by_id(user_id):
    """
    根据用户ID查询用户实体
    :param user_id: 用户ID
    :return: User实体
    """
    try:
        with db.get_session() as session:
            return session.query(User).filter(User.user_id == user_id).first()
    except OperationalError as e:
        logger.info("query_user_by_id errorMsg= {} ".format(e))
        return None


def insert_user(user):
    """
    插入一个User实体
    :param user: User实体
    """
    try:
        db.session.add(user)
        db.session.flush()  # 刷新以获取数据库生成的ID
        db.session.commit()
    except OperationalError as e:
        logger.info("insert_user errorMsg= {} ".format(e))
        db.session.rollback()
        raise


def update_user_by_id(user):
    """
    根据ID更新用户信息
    :param user: User实体
    """
    try:
        existing_user = query_user_by_id(user.user_id)
        if existing_user is None:
            return
        # 更新用户信息
        if user.nickname is not None:
            existing_user.nickname = user.nickname
        if user.avatar_url is not None:
            existing_user.avatar_url = user.avatar_url
        if user.name is not None:
            existing_user.name = user.name
        if user.work_id is not None:
            existing_user.work_id = user.work_id
        if user.phone_number is not None:
            existing_user.phone_number = user.phone_number
        if user.role is not None:
            # 如果传入的是字符串，转换为对应的整数值
            if isinstance(user.role, str):
                role_value = User.get_role_value(user.role)
                if role_value is not None:
                    existing_user.role = role_value
            elif isinstance(user.role, int):
                existing_user.role = user.role
        if user.verification_status is not None:
            existing_user.verification_status = user.verification_status
        if user.verification_materials is not None:
            existing_user.verification_materials = user.verification_materials
        if user.community_id is not None:
            existing_user.community_id = user.community_id
        if user.status is not None:
            # 如果传入的是字符串，转换为对应的整数值
            if isinstance(user.status, str):
                status_value = User.get_status_value(user.status)
                if status_value is not None:
                    existing_user.status = status_value
            elif isinstance(user.status, int):
                existing_user.status = user.status
        existing_user.updated_at = user.updated_at or datetime.now()
        
        db.session.flush()
        db.session.commit()
    except OperationalError as e:
        logger.info("update_user_by_id errorMsg= {} ".format(e))


# 打卡规则相关数据访问方法
def query_checkin_rules_by_user_id(user_id):
    """
    根据用户ID查询打卡规则列表（排除已删除）
    :param user_id: 用户ID
    :return: 打卡规则列表
    """
    try:
        return CheckinRule.query.filter(
            CheckinRule.solo_user_id == user_id,
            CheckinRule.status != 2  # 排除已删除的规则
        ).all()
    except OperationalError as e:
        logger.info("query_checkin_rules_by_user_id errorMsg= {} ".format(e))
        return []


def query_checkin_rule_by_id(rule_id):
    """
    根据规则ID查询打卡规则
    :param rule_id: 规则ID
    :return: 打卡规则实体
    """
    try:
        return CheckinRule.query.get(rule_id)
    except OperationalError as e:
        logger.info("query_checkin_rule_by_id errorMsg= {} ".format(e))
        return None


def insert_checkin_rule(rule):
    """
    插入打卡规则
    :param rule: 打卡规则实体
    """
    try:
        db.session.add(rule)
        db.session.commit()
    except OperationalError as e:
        logger.info("insert_checkin_rule errorMsg= {} ".format(e))


def update_checkin_rule_by_id(rule):
    """
    根据ID更新打卡规则
    :param rule: 打卡规则实体
    """
    try:
        existing_rule = query_checkin_rule_by_id(rule.rule_id)
        if existing_rule is None:
            return
        # 更新规则信息
        if rule.rule_name is not None:
            existing_rule.rule_name = rule.rule_name
        if rule.icon_url is not None:
            existing_rule.icon_url = rule.icon_url
        if rule.frequency_type is not None:
            existing_rule.frequency_type = rule.frequency_type
        if rule.time_slot_type is not None:
            existing_rule.time_slot_type = rule.time_slot_type
        if rule.custom_time is not None:
            existing_rule.custom_time = rule.custom_time
        if rule.week_days is not None:
            existing_rule.week_days = rule.week_days
        if rule.status is not None:
            existing_rule.status = rule.status
        existing_rule.updated_at = rule.updated_at or datetime.now()
        
        db.session.flush()
        db.session.commit()
    except OperationalError as e:
        logger.info("update_checkin_rule_by_id errorMsg= {} ".format(e))


def delete_checkin_rule_by_id(rule_id):
    """
    根据ID软删除打卡规则
    :param rule_id: 规则ID
    :return: Boolean 是否删除成功
    :raises: ValueError 当规则不存在时
    """
    try:
        rule = CheckinRule.query.get(rule_id)
        if rule is None:
            raise ValueError(f"没有找到 id 为 {rule_id} 的打卡规则")
        
        # 软删除：设置状态为已删除，记录删除时间
        rule.status = 2  # 已删除
        rule.deleted_at = datetime.now()
        db.session.commit()
        return True
    except ValueError:
        raise  # 重新抛出ValueError
    except OperationalError as e:
        logger.info("delete_checkin_rule_by_id errorMsg= {} ".format(e))
        return False


# 打卡记录相关数据访问方法
def query_checkin_records_by_user_id_and_date(user_id, checkin_date=None):
    """
    根据用户ID和日期查询打卡记录
    :param user_id: 用户ID
    :param checkin_date: 打卡日期，默认为今天
    :return: 打卡记录列表
    """
    try:
        if checkin_date is None:
            checkin_date = date.today()
        
        # 查询当天的打卡记录
        return CheckinRecord.query.filter(
            CheckinRecord.solo_user_id == user_id,
            db.func.date(CheckinRecord.planned_time) == checkin_date
        ).all()
    except OperationalError as e:
        logger.info("query_checkin_records_by_user_id_and_date errorMsg= {} ".format(e))
        return []


def query_checkin_records_by_rule_id_and_date(rule_id, checkin_date=None):
    """
    根据规则ID和日期查询打卡记录
    :param rule_id: 规则ID
    :param checkin_date: 打卡日期，默认为今天
    :return: 打卡记录列表
    """
    try:
        if checkin_date is None:
            checkin_date = date.today()
        
        # 查询当天该规则的打卡记录
        return CheckinRecord.query.filter(
            CheckinRecord.rule_id == rule_id,
            db.func.date(CheckinRecord.planned_time) == checkin_date
        ).all()
    except OperationalError as e:
        logger.info("query_checkin_records_by_rule_id_and_date errorMsg= {} ".format(e))
        return []


def query_checkin_record_by_id(record_id):
    """
    根据记录ID查询打卡记录
    :param record_id: 记录ID
    :return: 打卡记录实体
    """
    try:
        return CheckinRecord.query.get(record_id)
    except OperationalError as e:
        logger.info("query_checkin_record_by_id errorMsg= {} ".format(e))
        return None


def insert_checkin_record(record):
    """
    插入打卡记录
    :param record: 打卡记录实体
    """
    try:
        db.session.add(record)
        db.session.commit()
    except OperationalError as e:
        logger.info("insert_checkin_record errorMsg= {} ".format(e))


def update_checkin_record_by_id(record):
    """
    根据ID更新打卡记录
    :param record: 打卡记录实体
    """
    try:
        existing_record = query_checkin_record_by_id(record.record_id)
        if existing_record is None:
            return
        # 更新记录信息
        if record.checkin_time is not None:
            existing_record.checkin_time = record.checkin_time
        if record.status is not None:
            existing_record.status = record.status
        existing_record.updated_at = record.updated_at or datetime.now()
        
        db.session.flush()
        db.session.commit()
    except OperationalError as e:
        logger.info("update_checkin_record_by_id errorMsg= {} ".format(e))


def query_checkin_records_by_user_and_date_range(user_id, start_date, end_date):
    """
    根据用户ID和日期范围查询打卡记录
    :param user_id: 用户ID
    :param start_date: 开始日期
    :param end_date: 结束日期
    :return: 打卡记录列表
    """
    try:
        return CheckinRecord.query.filter(
            CheckinRecord.solo_user_id == user_id,
            CheckinRecord.planned_time >= start_date,
            CheckinRecord.planned_time <= end_date
        ).order_by(CheckinRecord.planned_time.desc()).all()
    except OperationalError as e:
        logger.info("query_checkin_records_by_user_and_date_range errorMsg= {} ".format(e))
        return []


def query_checkin_records_by_supervisor_and_date_range(supervisor_user_id, start_date, end_date):
    """
    根据监护人ID和日期范围查询被监护人的打卡记录
    :param supervisor_user_id: 监护人用户ID
    :param start_date: 开始日期
    :param end_date: 结束日期
    :return: 打卡记录列表
    """
    try:
        from database.models import SupervisionRuleRelation
        from sqlalchemy import and_
        
        # 获取监督者可以监督的所有用户和规则
        relations = SupervisionRuleRelation.query.filter(
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
                specific_rules.append(relation.rule_id)
        
        # 构建查询条件
        all_records = []
        
        # 查询可以监督所有规则的用户的记录
        if all_rules_users:
            all_records.extend(CheckinRecord.query.join(CheckinRule).filter(
                CheckinRecord.solo_user_id.in_(list(all_rules_users)),
                CheckinRecord.planned_time >= start_date,
                CheckinRecord.planned_time <= end_date
            ).all())
        
        # 查询可以监督特定规则的记录
        if specific_rules:
            all_records.extend(CheckinRecord.query.filter(
                CheckinRecord.rule_id.in_(specific_rules),
                CheckinRecord.planned_time >= start_date,
                CheckinRecord.planned_time <= end_date
            ).all())
        
        return list(set(all_records))  # 去重
    except OperationalError as e:
        logger.info("query_checkin_records_by_supervisor_and_date_range errorMsg= {} ".format(e))
        return []


def query_unchecked_users_by_date(checkin_date=None):
    """
    查询指定日期未打卡的用户
    :param checkin_date: 检查日期，默认为今天
    :return: 未打卡用户列表
    """
    try:
        if checkin_date is None:
            checkin_date = date.today()
        
        # 获取所有当天应打卡的规则
        rules_for_date = db.session.query(
            CheckinRule.solo_user_id,
            CheckinRule.rule_id
        ).join(
            User
        ).filter(
            # 规则启用
            CheckinRule.status == 1
        ).all()
        
        # 对于每个规则，检查是否已打卡
        unchecked_users = []
        for rule in rules_for_date:
            # 检查该规则当天的打卡情况
            records = CheckinRecord.query.filter(
                CheckinRecord.rule_id == rule.rule_id,
                db.func.date(CheckinRecord.planned_time) == checkin_date,
                CheckinRecord.status == 1  # 已打卡
            ).count()
            
            # 如果没有打卡记录，则该用户该规则未打卡
            if records == 0:
                unchecked_users.append({
                    'user_id': rule.solo_user_id,
                    'rule_id': rule.rule_id
                })
        
        return unchecked_users
    except OperationalError as e:
        logger.info("query_unchecked_users_by_date errorMsg= {} ".format(e))
        return []


# 监督规则关系数据访问方法
def query_supervision_relations_by_solo_user(solo_user_id):
    """
    根据被监督用户ID查询监督关系列表
    :param solo_user_id: 被监督用户ID
    :return: 监督关系列表
    """
    try:
        from database.models import SupervisionRuleRelation
        return SupervisionRuleRelation.query.filter(
            SupervisionRuleRelation.solo_user_id == solo_user_id
        ).all()
    except OperationalError as e:
        logger.info("query_supervision_relations_by_solo_user errorMsg= {} ".format(e))
        return []


def query_supervision_relations_by_supervisor(supervisor_user_id):
    """
    根据监督者用户ID查询监督关系列表
    :param supervisor_user_id: 监督者用户ID
    :return: 监督关系列表
    """
    try:
        from database.models import SupervisionRuleRelation
        return SupervisionRuleRelation.query.filter(
            SupervisionRuleRelation.supervisor_user_id == supervisor_user_id
        ).all()
    except OperationalError as e:
        logger.info("query_supervision_relations_by_supervisor errorMsg= {} ".format(e))
        return []


def query_supervision_relations_by_user_and_rule(solo_user_id, supervisor_user_id, rule_id=None):
    """
    根据用户和规则查询监督关系
    :param solo_user_id: 被监督用户ID
    :param supervisor_user_id: 监督者用户ID
    :param rule_id: 规则ID，如果为None则表示查询所有规则的监督关系
    :return: 监督关系列表
    """
    try:
        from database.models import SupervisionRuleRelation
        query = SupervisionRuleRelation.query.filter(
            SupervisionRuleRelation.solo_user_id == solo_user_id,
            SupervisionRuleRelation.supervisor_user_id == supervisor_user_id
        )
        
        if rule_id is not None:
            query = query.filter(
                (SupervisionRuleRelation.rule_id == rule_id) | 
                (SupervisionRuleRelation.rule_id.is_(None))
            )
        
        return query.all()
    except OperationalError as e:
        logger.info("query_supervision_relations_by_user_and_rule errorMsg= {} ".format(e))
        return []


def query_pending_supervision_invitations_by_supervisor(supervisor_user_id):
    """
    查询指定监督者收到的待处理邀请
    :param supervisor_user_id: 监督者用户ID
    :return: 待处理邀请列表
    """
    try:
        from database.models import SupervisionRuleRelation
        return SupervisionRuleRelation.query.filter(
            SupervisionRuleRelation.supervisor_user_id == supervisor_user_id,
            SupervisionRuleRelation.status == 1  # 待同意
        ).all()
    except OperationalError as e:
        logger.info("query_pending_supervision_invitations_by_supervisor errorMsg= {} ".format(e))
        return []


def insert_supervision_relation(relation):
    """
    插入监督关系
    :param relation: 监督关系实体
    """
    try:
        from database.models import SupervisionRuleRelation
        db.session.add(relation)
        db.session.commit()
    except OperationalError as e:
        logger.info("insert_supervision_relation errorMsg= {} ".format(e))


def update_supervision_relation_by_id(relation):
    """
    根据ID更新监督关系
    :param relation: 监督关系实体
    """
    try:
        from database.models import SupervisionRuleRelation
        existing_relation = SupervisionRuleRelation.query.get(relation.relation_id)
        if existing_relation is None:
            return
        # 更新关系信息
        if relation.status is not None:
            existing_relation.status = relation.status
        existing_relation.updated_at = relation.updated_at or datetime.now()
        
        db.session.flush()
        db.session.commit()
    except OperationalError as e:
        logger.info("update_supervision_relation_by_id errorMsg= {} ".format(e))


def delete_supervision_relation_by_id(relation_id):
    """
    根据ID删除监督关系
    :param relation_id: 关系ID
    """
    try:
        from database.models import SupervisionRuleRelation
        relation = SupervisionRuleRelation.query.get(relation_id)
        if relation is None:
            return
        db.session.delete(relation)
        db.session.commit()
    except OperationalError as e:
        logger.info("delete_supervision_relation_by_id errorMsg= {} ".format(e))


def query_supervised_rules_for_supervisor(supervisor_user_id, solo_user_id):
    """
    查询监督者可以监督的特定用户的规则列表
    :param supervisor_user_id: 监督者用户ID
    :param solo_user_id: 被监督用户ID
    :return: 规则列表
    """
    try:
        from database.models import SupervisionRuleRelation
        relations = SupervisionRuleRelation.query.filter(
            SupervisionRuleRelation.supervisor_user_id == supervisor_user_id,
            SupervisionRuleRelation.solo_user_id == solo_user_id,
            SupervisionRuleRelation.status == 2  # 已同意
        ).all()
        
        rules = []
        for relation in relations:
            if relation.rule_id is None:  # 监督所有规则
                from database.models import CheckinRule
                rules.extend(CheckinRule.query.filter(
                    CheckinRule.solo_user_id == solo_user_id,
                    CheckinRule.status != 2  # 排除已删除的规则
                ).all())
            else:  # 监督特定规则
                from database.models import CheckinRule
                rule = CheckinRule.query.get(relation.rule_id)
                if rule:
                    rules.append(rule)
        return list(set(rules))  # 去重
    except OperationalError as e:
        logger.info("query_supervised_rules_for_supervisor errorMsg= {} ".format(e))
        return []


def query_checkin_records_by_supervisor_and_date_range(supervisor_user_id, start_date, end_date):
    """
    根据监督者ID和日期范围查询被监督用户的打卡记录
    :param supervisor_user_id: 监督者用户ID
    :param start_date: 开始日期
    :param end_date: 结束日期
    :return: 打卡记录列表
    """
    try:
        from database.models import SupervisionRuleRelation
        from sqlalchemy import and_
        
        # 获取监督者可以监督的所有用户和规则
        relations = SupervisionRuleRelation.query.filter(
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
                specific_rules.append(relation.rule_id)
        
        # 构建查询条件
        all_records = []
        
        # 查询可以监督所有规则的用户的记录
        if all_rules_users:
            all_records.extend(CheckinRecord.query.join(CheckinRule).filter(
                CheckinRecord.solo_user_id.in_(list(all_rules_users)),
                CheckinRecord.planned_time >= start_date,
                CheckinRecord.planned_time <= end_date
            ).all())
        
        # 查询可以监督特定规则的记录
        if specific_rules:
            all_records.extend(CheckinRecord.query.filter(
                CheckinRecord.rule_id.in_(specific_rules),
                CheckinRecord.planned_time >= start_date,
                CheckinRecord.planned_time <= end_date
            ).all())
        
        return list(set(all_records))  # 去重
    except OperationalError as e:
        logger.info("query_checkin_records_by_supervisor_and_date_range errorMsg= {} ".format(e))
        return []
