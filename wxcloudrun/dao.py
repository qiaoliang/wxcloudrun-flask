import logging
from datetime import datetime, date
from sqlalchemy.exc import OperationalError
from sqlalchemy import and_, or_

from wxcloudrun import db
from wxcloudrun.model import Counters, User, CheckinRule, CheckinRecord, RuleSupervision

# 初始化日志
logger = logging.getLogger('log')


def query_counterbyid(id):
    """
    根据ID查询Counter实体
    :param id: Counter的ID
    :return: Counter实体
    """
    try:
        result = Counters.query.filter(Counters.id == id).first()
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
        logger.info(f"delete_counterbyid: 准备删除ID为 {id} 的计数器")
        counter = Counters.query.get(id)
        if counter is None:
            logger.warning(f"delete_counterbyid: 未找到ID为 {id} 的计数器进行删除")
            return
        logger.info(f"delete_counterbyid: 找到计数器，值为 {counter.count}")
        db.session.delete(counter)
        db.session.commit()
        logger.info(f"delete_counterbyid: 成功删除ID为 {id} 的计数器")
    except OperationalError as e:
        logger.error("delete_counterbyid errorMsg= {} ".format(e))


def insert_counter(counter):
    """
    插入一个Counter实体
    :param counter: Counters实体
    """
    try:
        logger.info(f"insert_counter: 准备插入计数器，ID: {counter.id}, 值: {counter.count}")
        db.session.add(counter)
        db.session.commit()
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
        return User.query.filter(User.wechat_openid == openid).first()
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
        return User.query.filter(User.user_id == user_id).first()
    except OperationalError as e:
        logger.info("query_user_by_id errorMsg= {} ".format(e))
        return None


def query_user_by_phone(phone_number):
    """
    根据手机号码查询用户实体
    :param phone_number: 手机号码（已加密）
    :return: User实体
    """
    try:
        return User.query.filter(User.phone_number == phone_number).first()
    except OperationalError as e:
        logger.info("query_user_by_phone errorMsg= {} ".format(e))
        return None


def insert_user(user):
    """
    插入一个User实体
    :param user: User实体
    """
    try:
        db.session.add(user)
        db.session.commit()
    except OperationalError as e:
        logger.info("insert_user errorMsg= {} ".format(e))


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
    根据用户ID查询打卡规则列表
    :param user_id: 用户ID
    :return: 打卡规则列表
    """
    try:
        return CheckinRule.query.filter(
            CheckinRule.solo_user_id == user_id,
            CheckinRule.status == 1  # 只查询启用的规则
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
    根据ID删除打卡规则
    :param rule_id: 规则ID
    """
    try:
        rule = CheckinRule.query.get(rule_id)
        if rule is None:
            return
        db.session.delete(rule)
        db.session.commit()
    except OperationalError as e:
        logger.info("delete_checkin_rule_by_id errorMsg= {} ".format(e))


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
    # 注意：这需要关联SupervisionRelation表，目前未实现，暂返回空列表
    # 未来需要实现监护关系表后，才能查询被监护人的打卡记录
    try:
        # 这里只是一个占位实现，实际需要关联监护关系表
        return []
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
            # 只考虑独居者
            User.role == 1,
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


# ==================== RuleSupervision DAO 方法 ====================

def create_rule_supervision(rule_id, solo_user_id, supervisor_user_id, invitation_message, invited_by_user_id):
    """
    创建规则监护关系
    :param rule_id: 打卡规则ID
    :param solo_user_id: 独居者用户ID
    :param supervisor_user_id: 监护人用户ID
    :param invitation_message: 邀请消息
    :param invited_by_user_id: 邀请人用户ID
    :return: RuleSupervision对象或None
    """
    try:
        logger.info(f"create_rule_supervision: 创建监护关系 rule_id={rule_id}, solo_user_id={solo_user_id}, supervisor_user_id={supervisor_user_id}")
        
        supervision = RuleSupervision(
            rule_id=rule_id,
            solo_user_id=solo_user_id,
            supervisor_user_id=supervisor_user_id,
            invitation_message=invitation_message,
            invited_by_user_id=invited_by_user_id,
            status=0  # 待确认状态
        )
        
        db.session.add(supervision)
        db.session.commit()
        
        logger.info(f"create_rule_supervision: 成功创建监护关系，ID={supervision.rule_supervision_id}")
        return supervision
    except OperationalError as e:
        logger.error(f"create_rule_supervision errorMsg= {e}")
        db.session.rollback()
        return None


def get_rule_supervision_by_id(supervision_id):
    """
    根据ID获取规则监护关系
    :param supervision_id: 监护关系ID
    :return: RuleSupervision对象或None
    """
    try:
        supervision = RuleSupervision.query.filter(
            RuleSupervision.rule_supervision_id == supervision_id
        ).first()
        logger.info(f"get_rule_supervision_by_id: 查询ID {supervision_id} - {'找到' if supervision else '未找到'}")
        return supervision
    except OperationalError as e:
        logger.error(f"get_rule_supervision_by_id errorMsg= {e}")
        return None


def get_rule_supervisions(rule_id, status=None):
    """
    获取指定规则的监护关系列表
    :param rule_id: 打卡规则ID
    :param status: 状态过滤（可选）
    :return: 监护关系列表
    """
    try:
        query = RuleSupervision.query.filter(RuleSupervision.rule_id == rule_id)
        
        if status is not None:
            query = query.filter(RuleSupervision.status == status)
        
        supervisions = query.order_by(RuleSupervision.created_at.desc()).all()
        logger.info(f"get_rule_supervisions: 规则ID {rule_id} 找到 {len(supervisions)} 个监护关系")
        return supervisions
    except OperationalError as e:
        logger.error(f"get_rule_supervisions errorMsg= {e}")
        return []


def get_user_supervisions(user_id, supervision_type='received', status=None):
    """
    获取用户的监护关系列表
    :param user_id: 用户ID
    :param supervision_type: 监护类型 'received'(收到的邀请) 或 'sent'(发出的邀请)
    :param status: 状态过滤（可选）
    :return: 监护关系列表
    """
    try:
        if supervision_type == 'received':
            # 收到的邀请（作为监护人）
            query = RuleSupervision.query.filter(RuleSupervision.supervisor_user_id == user_id)
        else:
            # 发出的邀请（作为独居者或邀请人）
            query = RuleSupervision.query.filter(
                or_(
                    RuleSupervision.solo_user_id == user_id,
                    RuleSupervision.invited_by_user_id == user_id
                )
            )
        
        if status is not None:
            query = query.filter(RuleSupervision.status == status)
        
        supervisions = query.order_by(RuleSupervision.created_at.desc()).all()
        logger.info(f"get_user_supervisions: 用户ID {user_id}, 类型 {supervision_type} 找到 {len(supervisions)} 个监护关系")
        return supervisions
    except OperationalError as e:
        logger.error(f"get_user_supervisions errorMsg= {e}")
        return []


def get_supervisor_active_rules(supervisor_user_id):
    """
    获取监护人负责的所有活跃规则
    :param supervisor_user_id: 监护人用户ID
    :return: 规则列表，包含今日打卡状态
    """
    try:
        from datetime import datetime
        
        # 获取监护人的所有活跃监护关系
        supervisions = RuleSupervision.query.filter(
            RuleSupervision.supervisor_user_id == supervisor_user_id,
            RuleSupervision.status == 1  # 已确认状态
        ).all()
        
        result = []
        today = datetime.now().date()
        
        for supervision in supervisions:
            # 获取规则信息
            rule = supervision.rule
            solo_user = supervision.solo_user
            
            # 查询今日打卡状态
            today_record = CheckinRecord.query.filter(
                CheckinRecord.rule_id == rule.rule_id,
                db.func.date(CheckinRecord.planned_time) == today
            ).first()
            
            # 获取最近打卡记录
            last_record = CheckinRecord.query.filter(
                CheckinRecord.rule_id == rule.rule_id,
                CheckinRecord.status == 1  # 已打卡
            ).order_by(CheckinRecord.checkin_time.desc()).first()
            
            result.append({
                'rule_supervision_id': supervision.rule_supervision_id,
                'rule': {
                    'rule_id': rule.rule_id,
                    'rule_name': rule.rule_name,
                    'icon_url': rule.icon_url
                },
                'solo_user': {
                    'user_id': solo_user.user_id,
                    'nickname': solo_user.nickname,
                    'avatar_url': solo_user.avatar_url
                },
                'today_status': 'checked' if today_record and today_record.status == 1 else 'unchecked',
                'last_checkin': last_record.checkin_time.isoformat() if last_record else None
            })
        
        logger.info(f"get_supervisor_active_rules: 监护人 {supervisor_user_id} 负责的规则数量 {len(result)}")
        return result
    except OperationalError as e:
        logger.error(f"get_supervisor_active_rules errorMsg= {e}")
        return []


def check_existing_supervision(rule_id, supervisor_user_id):
    """
    检查是否已存在监护关系
    :param rule_id: 打卡规则ID
    :param supervisor_user_id: 监护人用户ID
    :return: RuleSupervision对象或None
    """
    try:
        supervision = RuleSupervision.query.filter(
            RuleSupervision.rule_id == rule_id,
            RuleSupervision.supervisor_user_id == supervisor_user_id,
            RuleSupervision.status.in_([0, 1])  # 待确认或已确认状态
        ).first()
        
        logger.info(f"check_existing_supervision: 规则 {rule_id} 监护人 {supervisor_user_id} - {'存在' if supervision else '不存在'}监护关系")
        return supervision
    except OperationalError as e:
        logger.error(f"check_existing_supervision errorMsg= {e}")
        return None


def update_supervision_status(supervision_id, status, response_message=None):
    """
    更新监护关系状态
    :param supervision_id: 监护关系ID
    :param status: 新状态
    :param response_message: 响应消息（可选）
    :return: RuleSupervision对象或None
    """
    try:
        supervision = RuleSupervision.query.filter(
            RuleSupervision.rule_supervision_id == supervision_id
        ).first()
        
        if not supervision:
            logger.warning(f"update_supervision_status: 未找到监护关系 {supervision_id}")
            return None
        
        supervision.status = status
        
        if status in [1, 2]:  # 已确认或已拒绝时设置响应时间
            supervision.responded_at = datetime.now()
        
        # 如果有响应消息，可以添加到邀请消息中（或创建新字段存储）
        if response_message:
            supervision.invitation_message = f"{supervision.invitation_message or ''}\n\n响应: {response_message}"
        
        db.session.commit()
        
        logger.info(f"update_supervision_status: 成功更新监护关系 {supervision_id} 状态为 {status}")
        return supervision
    except OperationalError as e:
        logger.error(f"update_supervision_status errorMsg= {e}")
        db.session.rollback()
        return None


def get_supervisor_count(rule_id):
    """
    获取规则的监护人数量
    :param rule_id: 打卡规则ID
    :return: 监护人数量
    """
    try:
        count = RuleSupervision.query.filter(
            RuleSupervision.rule_id == rule_id,
            RuleSupervision.status == 1  # 只计算已确认的监护人
        ).count()
        
        logger.info(f"get_supervisor_count: 规则 {rule_id} 有 {count} 个监护人")
        return count
    except OperationalError as e:
        logger.error(f"get_supervisor_count errorMsg= {e}")
        return 0


def delete_rule_supervision(supervision_id):
    """
    删除规则监护关系
    :param supervision_id: 监护关系ID
    :return: 是否成功
    """
    try:
        supervision = RuleSupervision.query.filter(
            RuleSupervision.rule_supervision_id == supervision_id
        ).first()
        
        if not supervision:
            logger.warning(f"delete_rule_supervision: 未找到监护关系 {supervision_id}")
            return False
        
        db.session.delete(supervision)
        db.session.commit()
        
        logger.info(f"delete_rule_supervision: 成功删除监护关系 {supervision_id}")
        return True
    except OperationalError as e:
        logger.error(f"delete_rule_supervision errorMsg= {e}")
        db.session.rollback()
        return False
