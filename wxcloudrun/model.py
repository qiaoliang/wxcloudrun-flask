from sqlalchemy import and_
from datetime import datetime
import os

from sqlalchemy import Column, Integer, String, DateTime, Text, text
from wxcloudrun import db  # 导入db对象
from datetime import datetime


class Counters(db.Model):
    __tablename__ = 'Counters'

    id = Column(Integer, primary_key=True)
    count = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


# 用户表
class User(db.Model):
    # 设置结构体表格名称
    __tablename__ = 'users'

    # 设定结构体对应表格的字段
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    wechat_openid = db.Column(
        db.String(128), unique=True, nullable=False, comment='微信OpenID，唯一标识用户')
    phone_number = db.Column(
        db.String(20), unique=True, comment='手机号码，可用于登录和联系')
    nickname = db.Column(db.String(100), comment='用户昵称')
    avatar_url = db.Column(db.String(500), comment='用户头像URL')
    name = db.Column(db.String(100), comment='真实姓名')
    work_id = db.Column(db.String(50), comment='工号或身份证号')

    # 使用整数类型存储角色和状态，避免在不同数据库间使用不同字段类型
    # 角色: 1-独居者, 2-监护人, 3-社区工作人员（保留用于兼容，逐步过渡到权限组合）
    role = db.Column(db.Integer, nullable=False,
                     comment='用户角色：1-独居者/2-监护人/3-社区工作人员')
    # 状态: 1-正常, 2-禁用
    status = db.Column(db.Integer, default=1, comment='用户状态：1-正常/2-禁用')

    # 验证状态: 0-未申请, 1-待审核, 2-已通过, 3-已拒绝
    verification_status = db.Column(
        db.Integer, default=0, comment='验证状态：0-未申请/1-待审核/2-已通过/3-已拒绝')
    verification_materials = db.Column(db.Text, comment='验证材料URL')

    # 权限组合字段：用于替代互斥角色模型
    is_solo_user = db.Column(db.Boolean, default=True, comment='是否为打卡人')
    is_supervisor = db.Column(db.Boolean, default=False, comment='是否为监护人')
    is_community_worker = db.Column(
        db.Boolean, default=False, comment='是否为社区工作人员')

    community_id = db.Column(db.Integer, comment='所属社区ID，仅社区工作人员需要')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now,
                           onupdate=datetime.now, comment='更新时间')

    # 索引
    __table_args__ = (
        db.Index('idx_openid', 'wechat_openid'),  # 微信OpenID索引，支持快速登录查询
        db.Index('idx_phone', 'phone_number'),    # 手机号索引，支持手机号登录
        db.Index('idx_role', 'role'),             # 角色索引，支持按角色查询
    )

    # 角色映射
    ROLE_MAPPING = {
        1: 'solo',
        2: 'supervisor',
        3: 'community'
    }

    # 状态映射
    STATUS_MAPPING = {
        0: 'not_applied',
        1: 'pending',
        2: 'verified',
        3: 'rejected'
    }

    @property
    def role_name(self):
        """获取角色名称"""
        return self.ROLE_MAPPING.get(self.role, 'unknown')

    @property
    def status_name(self):
        """获取状态名称"""
        return self.STATUS_MAPPING.get(self.status, 'unknown')

    @classmethod
    def get_role_value(cls, role_name):
        """根据角色名称获取角色值"""
        for value, name in cls.ROLE_MAPPING.items():
            if name == role_name:
                return value
        return None

    @classmethod
    def get_status_value(cls, status_name):
        """根据状态名称获取状态值"""
        for value, name in cls.STATUS_MAPPING.items():
            if name == status_name:
                return value
        return None


# 打卡规则表
class CheckinRule(db.Model):
    # 设置结构体表格名称
    __tablename__ = 'checkin_rules'

    # 设定结构体对应表格的字段
    rule_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    solo_user_id = db.Column(db.Integer, db.ForeignKey(
        'users.user_id'), nullable=False, comment='独居者用户ID')
    rule_name = db.Column(db.String(100), nullable=False,
                          comment='打卡规则名称，如：起床打卡、早餐打卡等')
    icon_url = db.Column(db.String(500), comment='打卡事项图标URL')

    # 频率类型: 0-每天, 1-每周, 2-工作日, 3-自定义
    frequency_type = db.Column(
        db.Integer, nullable=False, default=0, comment='打卡频率类型：0-每天/1-每周/2-工作日/3-自定义')

    # 时间段类型: 1-上午, 2-下午, 3-晚上, 4-自定义时间
    time_slot_type = db.Column(
        db.Integer, nullable=False, default=4, comment='时间段类型：1-上午/2-下午/3-晚上/4-自定义时间')

    # 自定义时间（当time_slot_type为4时使用）
    custom_time = db.Column(db.Time, comment='自定义打卡时间')
    # 自定义日期范围（当frequency_type为3时使用）
    custom_start_date = db.Column(db.Date, comment='自定义开始日期')
    custom_end_date = db.Column(db.Date, comment='自定义结束日期')

    # 一周中的天（当frequency_type为1时使用，使用位掩码表示周几）
    week_days = db.Column(db.Integer, default=127,
                          comment='一周中的天（位掩码表示）：默认127表示周一到周日')

    # 规则状态：1-启用, 0-禁用
    status = db.Column(db.Integer, default=1, comment='规则状态：1-启用/0-禁用')

    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now,
                           onupdate=datetime.now, comment='更新时间')

    # 关联用户
    user = db.relationship(
        'User', backref=db.backref('checkin_rules', lazy=True))

    # 索引
    __table_args__ = (
        db.Index('idx_checkin_rules_solo_user', 'solo_user_id'),  # 用户ID索引
    )


# 打卡记录表
class CheckinRecord(db.Model):
    # 设置结构体表格名称
    __tablename__ = 'checkin_records'

    # 设定结构体对应表格的字段
    record_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rule_id = db.Column(db.Integer, db.ForeignKey(
        'checkin_rules.rule_id'), nullable=False, comment='打卡规则ID')
    solo_user_id = db.Column(db.Integer, db.ForeignKey(
        'users.user_id'), nullable=False, comment='独居者用户ID')
    checkin_time = db.Column(db.DateTime, comment='实际打卡时间')

    # 状态: 1-checked(已打卡), 0-missed(未打卡), 2-revoked(已撤销)
    status = db.Column(db.Integer, default=0, comment='状态：0-未打卡/1-已打卡/2-已撤销')

    planned_time = db.Column(db.DateTime, nullable=False, comment='计划打卡时间')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now,
                           onupdate=datetime.now, comment='更新时间')

    # 关联规则和用户
    rule = db.relationship('CheckinRule', backref=db.backref(
        'checkin_records', lazy=True))
    user = db.relationship('User', backref=db.backref(
        'checkin_records', lazy=True))

    # 索引
    __table_args__ = (
        db.Index('idx_checkin_records_rule', 'rule_id'),  # 规则ID索引
        db.Index('idx_checkin_records_solo_user', 'solo_user_id'),  # 用户ID索引
        db.Index('idx_checkin_records_planned_time', 'planned_time'),  # 计划时间索引
    )

    # 状态映射
    STATUS_MAPPING = {
        0: 'missed',
        1: 'checked',
        2: 'revoked'
    }

    @property
    def status_name(self):
        """获取状态名称"""
        return self.STATUS_MAPPING.get(self.status, 'unknown')

    @classmethod
    def get_status_value(cls, status_name):
        """根据状态名称获取状态值"""
        for value, name in cls.STATUS_MAPPING.items():
            if name == status_name:
                return value
        return None


# 监督规则关系表 - 连接用户和规则的监督关系
class SupervisionRuleRelation(db.Model):
    # 设置结构体表格名称
    __tablename__ = 'supervision_rule_relations'

    # 设定结构体对应表格的字段
    relation_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    solo_user_id = db.Column(db.Integer, db.ForeignKey(
        'users.user_id'), nullable=False, comment='被监督用户ID')
    supervisor_user_id = db.Column(db.Integer, db.ForeignKey(
        'users.user_id'), nullable=True, comment='监督者用户ID（链接邀请时可为空，待绑定）')
    rule_id = db.Column(db.Integer, db.ForeignKey(
        'checkin_rules.rule_id'), nullable=True, comment='具体规则ID，为空表示监督所有规则')
    status = db.Column(db.Integer, default=1,
                       comment='关系状态：1-待同意/2-已同意/3-已拒绝/4-已移除')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now,
                           onupdate=datetime.now, comment='更新时间')
    invite_token = db.Column(db.String(64), unique=True,
                             nullable=True, comment='邀请链接token')
    invite_expires_at = db.Column(db.DateTime, nullable=True, comment='邀请过期时间')

    # 关联用户和规则
    solo_user = db.relationship('User', foreign_keys=[
                                solo_user_id], backref=db.backref('supervised_by_relations', lazy=True))
    supervisor_user = db.relationship('User', foreign_keys=[
                                      supervisor_user_id], backref=db.backref('supervising_relations', lazy=True))
    rule = db.relationship('CheckinRule', backref=db.backref(
        'supervision_relations', lazy=True))

    # 索引
    __table_args__ = (
        db.Index('idx_solo_supervisor', 'solo_user_id',
                 'supervisor_user_id'),  # 用户监督关系索引
        db.Index('idx_supervisor_rule',
                 'supervisor_user_id', 'rule_id'),  # 监督者规则索引
    )

    # 状态映射
    STATUS_MAPPING = {
        1: 'pending',
        2: 'approved',
        3: 'rejected',
        4: 'removed'
    }

    @property
    def status_name(self):
        """获取状态名称"""
        return self.STATUS_MAPPING.get(self.status, 'unknown')

    @classmethod
    def get_status_value(cls, status_name):
        """根据状态名称获取状态值"""
        for value, name in cls.STATUS_MAPPING.items():
            if name == status_name:
                return value
        return None


# 更新User模型，增加方法以支持新的角色系统语义


def can_supervise_user(self, other_user_id):
    """检查当前用户是否可以监督指定用户"""
    # 检查是否存在有效的监督关系
    relation = SupervisionRuleRelation.query.filter(
        and_(
            SupervisionRuleRelation.supervisor_user_id == self.user_id,
            SupervisionRuleRelation.solo_user_id == other_user_id,
            SupervisionRuleRelation.status == 2  # 已同意
        )
    ).first()
    return relation is not None


def can_supervise_rule(self, rule_id):
    """检查当前用户是否可以监督指定规则"""
    # 检查是否存在监督特定规则的关系，或监督该用户所有规则的关系
    relation = SupervisionRuleRelation.query.filter(
        and_(
            SupervisionRuleRelation.supervisor_user_id == self.user_id,
            SupervisionRuleRelation.status == 2,  # 已同意
            (SupervisionRuleRelation.rule_id == rule_id) | (
                SupervisionRuleRelation.rule_id.is_(None))
        )
    ).first()
    return relation is not None


def get_supervised_users(self):
    """获取当前用户监督的所有用户列表"""
    relations = SupervisionRuleRelation.query.filter(
        and_(
            SupervisionRuleRelation.supervisor_user_id == self.user_id,
            SupervisionRuleRelation.status == 2  # 已同意
        )
    ).distinct(SupervisionRuleRelation.solo_user_id).all()
    return [relation.solo_user for relation in relations]


def get_supervised_rules(self, solo_user_id):
    """获取当前用户监督的特定用户的规则列表"""
    relations = SupervisionRuleRelation.query.filter(
        and_(
            SupervisionRuleRelation.supervisor_user_id == self.user_id,
            SupervisionRuleRelation.solo_user_id == solo_user_id,
            SupervisionRuleRelation.status == 2  # 已同意
        )
    ).all()

    rules = []
    for relation in relations:
        if relation.rule_id is None:  # 监督所有规则
            rules.extend(CheckinRule.query.filter(
                CheckinRule.solo_user_id == solo_user_id,
                CheckinRule.status == 1  # 启用的规则
            ).all())
        else:  # 监督特定规则
            rule = CheckinRule.query.get(relation.rule_id)
            if rule:
                rules.append(rule)
    return list(set(rules))  # 去重


# 绑定方法到User类
User.can_supervise_user = can_supervise_user
User.can_supervise_rule = can_supervise_rule
User.get_supervised_users = get_supervised_users
User.get_supervised_rules = get_supervised_rules


# 分享链接表
class ShareLink(db.Model):
    __tablename__ = 'share_links'

    link_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    token = db.Column(db.String(64), unique=True,
                      nullable=False, comment='分享链接token')
    solo_user_id = db.Column(db.Integer, db.ForeignKey(
        'users.user_id'), nullable=False, comment='打卡人用户ID')
    rule_id = db.Column(db.Integer, db.ForeignKey(
        'checkin_rules.rule_id'), nullable=False, comment='打卡规则ID')
    expires_at = db.Column(db.DateTime, nullable=False, comment='过期时间')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now,
                           onupdate=datetime.now, comment='更新时间')

    solo_user = db.relationship(
        'User', backref=db.backref('share_links', lazy=True))
    rule = db.relationship(
        'CheckinRule', backref=db.backref('share_links', lazy=True))

    __table_args__ = (
        db.Index('idx_share_token', 'token'),
        db.Index('idx_share_solo_rule', 'solo_user_id', 'rule_id'),
    )


# 分享链接访问日志
class ShareLinkAccessLog(db.Model):
    __tablename__ = 'share_link_access_logs'

    log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    token = db.Column(db.String(64), nullable=False, comment='分享链接token')
    accessed_at = db.Column(db.DateTime, default=datetime.now, comment='访问时间')
    ip_address = db.Column(db.String(64), comment='访问者IP')
    user_agent = db.Column(db.String(512), comment='UA')
    supervisor_user_id = db.Column(
        db.Integer, nullable=True, comment='解析后关联的监督者ID')

    __table_args__ = (
        db.Index('idx_share_log_token', 'token'),
    )
