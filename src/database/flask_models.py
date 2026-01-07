"""
Flask-SQLAlchemy模型定义
从纯SQLAlchemy迁移到Flask-SQLAlchemy
优化关系定义：使用 back_populates 替代 backref，添加 lazy 加载策略
优化数据库索引：为外键字段和常用查询字段添加索引
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Date, Time, Float, CheckConstraint, UniqueConstraint, Index
from app.extensions import db

# 角色常量 - 定义在这里避免循环导入
class Role:
    """角色 ID 常量 - 用于代码判断"""
    UNSET = 0  # 未设置
    SOLO = 1  # 普通用户 (独居者)
    STAFF = 2  # 社区专员
    MANAGER = 3  # 社区主管
    SUPER_ADMIN = 4  # 超级系统管理员

class RoleName:
    """角色名称常量 - 用于显示"""
    UNSET = "未设置"
    SOLO = "普通用户"
    STAFF = "社区专员"
    MANAGER = "社区主管"
    SUPER_ADMIN = "超级系统管理员"

# role_id 到 role_name 的映射（用于显示）
ROLE_ID_TO_NAME = {
    Role.UNSET: RoleName.UNSET,
    Role.SOLO: RoleName.SOLO,
    Role.STAFF: RoleName.STAFF,
    Role.MANAGER: RoleName.MANAGER,
    Role.SUPER_ADMIN: RoleName.SUPER_ADMIN,
}

# 数据库约束使用的角色值列表（用于 CheckConstraint）
DB_ROLE_CONSTRAINT_VALUES = [Role.UNSET, Role.SOLO, Role.STAFF, Role.MANAGER, Role.SUPER_ADMIN]

class User(db.Model):
    """用户表 - Flask-SQLAlchemy版本"""
    __tablename__ = 'users'

    user_id = Column(db.Integer, primary_key=True)
    wechat_openid = Column(db.String(128), unique=True, nullable=True, comment='微信OpenID', index=True)
    phone_number = Column(db.String(20), comment='手机号码')
    phone_hash = Column(db.String(64), unique=True, nullable=True, comment='手机号哈希', index=True)
    nickname = Column(db.String(100), comment='用户昵称')
    avatar_url = Column(db.String(500), comment='用户头像URL')
    name = Column(db.String(100), comment='真实姓名')
    work_id = Column(db.String(50), comment='工号或身份证号')
    address = Column(db.String(200), comment='个人地址')
    motto = Column(db.String(100), comment='座右铭')
    emergency_contact_name = Column(db.String(20), comment='紧急联系人姓名')
    emergency_contact_phone = Column(db.String(20), comment='紧急联系人电话')
    emergency_contact_address = Column(db.String(100), comment='紧急联系人地址')
    password_hash = Column(db.String(128), comment='密码哈希')
    password_salt = Column(db.String(32), comment='密码盐')
    role = Column(db.Integer, nullable=False, comment='用户角色', index=True)
    status = Column(db.Integer, default=1, comment='用户状态', index=True)
    verification_status = Column(db.Integer, default=0, comment='验证状态')
    verification_materials = Column(db.Text, comment='验证材料')
    _is_community_worker = Column('is_community_worker', Boolean, default=False)
    community_id = Column(db.Integer, db.ForeignKey('communities.community_id', use_alter=True), index=True)
    community_joined_at = Column(db.DateTime, comment='加入当前社区的时间')
    refresh_token = Column(db.String(128), comment='刷新令牌')
    refresh_token_expire = Column(db.DateTime, comment='刷新令牌过期时间')
    created_at = Column(db.DateTime, default=datetime.now, index=True)
    updated_at = Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 索引优化和约束
    __table_args__ = (
        db.Index('idx_user_community_id', 'community_id'),
        db.Index('idx_user_role', 'role'),
        db.Index('idx_user_status', 'status'),
        db.Index('idx_user_created_at', 'created_at'),
        db.Index('idx_user_community_status', 'community_id', 'status'),
        db.Index('idx_user_role_status', 'role', 'status'),
        db.CheckConstraint(f'role IN ({", ".join(map(str, DB_ROLE_CONSTRAINT_VALUES))})', name='ck_user_role'),  # 0=未设置, 1=普通用户, 2=社区专员, 3=社区主管, 4=超级系统管理员
        db.CheckConstraint('status IN (0, 1, 2)', name='ck_user_status'),  # 0=禁用, 1=正常, 2=待验证
    )

    # 关系 - 使用 back_populates 替代 backref
    community = db.relationship('Community', foreign_keys=[community_id], back_populates='users', lazy='selectin')
    checkin_rules = db.relationship('CheckinRule', back_populates='user', lazy='selectin')
    checkin_records = db.relationship('CheckinRecord', foreign_keys='CheckinRecord.user_id', back_populates='user', lazy='dynamic')
    solo_checkin_records = db.relationship('CheckinRecord', foreign_keys='CheckinRecord.solo_user_id', back_populates='solo_user', lazy='dynamic')
    audit_logs = db.relationship('UserAuditLog', back_populates='user', lazy='dynamic')
    supervised_by_relations = db.relationship('SupervisionRuleRelation', foreign_keys='SupervisionRuleRelation.solo_user_id', back_populates='solo_user', lazy='dynamic')
    supervising_relations = db.relationship('SupervisionRuleRelation', foreign_keys='SupervisionRuleRelation.supervisor_user_id', back_populates='supervisor_user', lazy='dynamic')
    staff_roles = db.relationship('CommunityStaff', back_populates='user', lazy='selectin')
    community_applications = db.relationship('CommunityApplication', foreign_keys='CommunityApplication.user_id', back_populates='user', lazy='dynamic')
    processed_applications = db.relationship('CommunityApplication', foreign_keys='CommunityApplication.processed_by', back_populates='processor', lazy='dynamic')
    share_links = db.relationship('ShareLink', back_populates='solo_user', lazy='dynamic')
    created_communities = db.relationship('Community', foreign_keys='Community.creator_id', back_populates='creator', lazy='dynamic')
    created_events = db.relationship('CommunityEvent', foreign_keys='CommunityEvent.created_by', back_populates='creator', lazy='dynamic')
    targeted_events = db.relationship('CommunityEvent', foreign_keys='CommunityEvent.target_user_id', back_populates='target_user', lazy='dynamic')
    supports = db.relationship('EventMessage', back_populates='sender', lazy='dynamic')
    user_community_rules = db.relationship('UserCommunityRule', back_populates='user', lazy='selectin')

    # 角色映射 - 使用统一常量
    ROLE_MAPPING = ROLE_ID_TO_NAME

    # 状态映射
    STATUS_MAPPING = {
        0: '禁用',
        1: '正常',
        2: '待验证'
    }

    def __repr__(self):
        return f'<User {self.user_id}: {self.nickname}>'

    @property
    def role_name(self):
        return self.ROLE_MAPPING.get(self.role, '未知角色')

    @property
    def status_name(self):
        return self.STATUS_MAPPING.get(self.status, '未知状态')

    def set_password(self, password):
        """设置密码"""
        import hashlib
        import random
        self.password_salt = hashlib.md5(str(hash(random.random())).encode()).hexdigest()[:32]
        salted_password = f"{password}:{self.password_salt}"
        self.password_hash = hashlib.sha256(salted_password.encode()).hexdigest()

    def verify_password(self, password):
        """验证密码"""
        import hashlib
        if not self.password_hash or not self.password_salt:
            return False
        salted_password = f"{password}:{self.password_salt}"
        return self.password_hash == hashlib.sha256(salted_password.encode()).hexdigest()


class Community(db.Model):
    __tablename__ = 'communities'

    community_id = Column(db.Integer, primary_key=True)
    name = Column(db.String(100), nullable=False, unique=True, comment='社区名称')
    description = Column(db.Text, comment='社区描述')
    creator_id = Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True, comment='创建人ID', index=True)
    manager_id = Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True, comment='主管ID', index=True)
    status = Column(db.Integer, default=1, nullable=False, comment='社区状态', index=True)
    settings = Column(db.Text, comment='社区设置（JSON）')
    location = Column(db.String(200), comment='地理位置')
    location_lat = Column(db.Float, comment='纬度')
    location_lon = Column(db.Float, comment='经度')
    province = Column(db.String(50), comment='省份')
    city = Column(db.String(50), comment='城市')
    district = Column(db.String(50), comment='区县')
    street = Column(db.String(200), comment='街道')
    is_default = Column(db.Boolean, default=False, nullable=False, comment='是否默认社区', index=True)
    is_blackhouse = Column(db.Boolean, default=False, nullable=False, comment='是否黑屋社区', index=True)
    created_at = Column(db.DateTime, default=datetime.now, index=True)
    updated_at = Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 索引优化和约束
    __table_args__ = (
        db.Index('idx_community_creator_id', 'creator_id'),
        db.Index('idx_community_manager_id', 'manager_id'),
        db.Index('idx_community_status', 'status'),
        db.Index('idx_community_is_default', 'is_default'),
        db.Index('idx_community_is_blackhouse', 'is_blackhouse'),
        db.Index('idx_community_created_at', 'created_at'),
        db.Index('idx_community_status_is_default', 'status', 'is_default'),
        db.CheckConstraint('status IN (0, 1, 2)', name='ck_community_status'),  # 0=禁用, 1=启用, 2=删除
    )

    @property
    def settings_dict(self):
        """获取社区设置字典"""
        import json
        try:
            return json.loads(self.settings) if self.settings else {}
        except (json.JSONDecodeError, TypeError):
            return {}

    @settings_dict.setter
    def settings_dict(self, value):
        """设置社区设置字典"""
        import json
        self.settings = json.dumps(value) if value else None

    # 关系 - 使用 back_populates 替代 backref
    users = db.relationship('User', foreign_keys=[User.community_id], back_populates='community', lazy='dynamic')
    creator = db.relationship('User', foreign_keys=[creator_id], back_populates='created_communities', lazy='selectin')
    checkin_rules = db.relationship('CheckinRule', back_populates='community', lazy='dynamic')
    staff_members = db.relationship('CommunityStaff', back_populates='community', lazy='selectin')
    community_checkin_rules = db.relationship('CommunityCheckinRule', back_populates='community', lazy='dynamic')
    applications = db.relationship('CommunityApplication', back_populates='target_community', lazy='dynamic')
    events = db.relationship('CommunityEvent', back_populates='community', lazy='dynamic')

    # 状态映射
    STATUS_MAPPING = {
        0: 'disabled',
        1: 'enabled',
        2: 'deleted'
    }

    @property
    def status_name(self):
        """获取状态名称"""
        return self.STATUS_MAPPING.get(self.status, 'unknown')

    def __repr__(self):
        return f'<Community {self.community_id}: {self.name}>'


class CheckinRule(db.Model):
    __tablename__ = 'checkin_rules'

    rule_id = Column(db.Integer, primary_key=True)
    user_id = Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, index=True)
    community_id = Column(db.Integer, db.ForeignKey('communities.community_id'), nullable=True, comment='规则来源社区', index=True)
    rule_type = Column(db.String(50), nullable=False, default='personal', comment='规则类型: personal=个人规则, community=社区规则')
    rule_name = Column(db.String(100), nullable=False, comment='规则名称')
    icon_url = Column(db.String(500), comment='图标URL')
    frequency_type = Column(db.Integer, nullable=False, default=0, comment='频率类型')
    time_slot_type = Column(db.Integer, nullable=False, default=4, comment='时间段类型')
    custom_time = Column(db.Time, comment='自定义时间')
    custom_start_date = Column(db.Date, comment='自定义开始日期')
    custom_end_date = Column(db.Date, comment='自定义结束日期')
    week_days = Column(db.Integer, default=127, comment='周天数')
    status = Column(db.Integer, default=1, comment='规则状态: 0=停用, 1=启用, 2=删除', index=True)
    created_at = Column(db.DateTime, default=datetime.now, index=True)
    updated_at = Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 索引优化和约束
    __table_args__ = (
        db.Index('idx_checkin_rule_user_id', 'user_id'),
        db.Index('idx_checkin_rule_community_id', 'community_id'),
        db.Index('idx_checkin_rule_status', 'status'),
        db.Index('idx_checkin_rule_user_status', 'user_id', 'status'),
        db.Index('idx_checkin_rule_community_status', 'community_id', 'status'),
        db.Index('idx_checkin_rule_created_at', 'created_at'),
        db.CheckConstraint("rule_type IN ('personal', 'community')", name='ck_checkin_rule_type'),
        db.CheckConstraint('status IN (0, 1, 2)', name='ck_checkin_rule_status'),  # 0=停用, 1=启用, 2=删除
    )

    # 关系 - 使用 back_populates 替代 backref
    user = db.relationship('User', back_populates='checkin_rules', lazy='selectin')
    community = db.relationship('Community', back_populates='checkin_rules', lazy='selectin')
    records = db.relationship('CheckinRecord', back_populates='rule', lazy='dynamic')
    supervision_relations = db.relationship('SupervisionRuleRelation', back_populates='rule', lazy='dynamic')
    share_links = db.relationship('ShareLink', back_populates='rule', lazy='dynamic')

    def to_dict(self):
        """将模型对象转换为字典"""
        return {
            'rule_id': self.rule_id,
            'user_id': self.user_id,
            'community_id': self.community_id,
            'rule_type': self.rule_type,
            'rule_name': self.rule_name,
            'icon_url': self.icon_url,
            'frequency_type': self.frequency_type,
            'time_slot_type': self.time_slot_type,
            'custom_time': self.custom_time.isoformat() if self.custom_time else None,
            'custom_start_date': self.custom_start_date.isoformat() if self.custom_start_date else None,
            'custom_end_date': self.custom_end_date.isoformat() if self.custom_end_date else None,
            'week_days': self.week_days,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<CheckinRule {self.rule_id}: {self.rule_name}>'


class CheckinRecord(db.Model):
    """打卡记录表"""
    __tablename__ = 'checkin_records'

    record_id = Column(db.Integer, primary_key=True)
    user_id = Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, index=True)
    solo_user_id = Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True, comment='社区规则打卡用户ID', index=True)
    rule_id = Column(db.Integer, db.ForeignKey('checkin_rules.rule_id'), nullable=True, index=True)
    community_rule_id = Column(db.Integer, nullable=True, comment='社区规则ID', index=True)
    planned_time = Column(db.DateTime, nullable=False, comment='计划打卡时间', index=True)
    checkin_time = Column(db.DateTime, comment='实际打卡时间', index=True)
    checkin_type = Column(db.String(50), comment='打卡类型')
    content = Column(db.Text, comment='打卡内容')
    status = Column(db.Integer, default=0, comment='打卡状态: 0=未打卡, 1=已打卡, 2=已撤销', index=True)
    updated_at = Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    created_at = Column(db.DateTime, default=datetime.now, index=True)

    # 索引优化和约束
    __table_args__ = (
        db.Index('idx_checkin_record_user_id', 'user_id'),
        db.Index('idx_checkin_record_solo_user_id', 'solo_user_id'),
        db.Index('idx_checkin_record_rule_id', 'rule_id'),
        db.Index('idx_checkin_record_community_rule_id', 'community_rule_id'),
        db.Index('idx_checkin_record_planned_time', 'planned_time'),
        db.Index('idx_checkin_record_checkin_time', 'checkin_time'),
        db.Index('idx_checkin_record_status', 'status'),
        db.Index('idx_checkin_record_user_status', 'user_id', 'status'),
        db.Index('idx_checkin_record_rule_status', 'rule_id', 'status'),
        db.Index('idx_checkin_record_planned_time_status', 'planned_time', 'status'),
        db.CheckConstraint('status IN (0, 1, 2)', name='ck_checkin_record_status'),  # 0=未打卡, 1=已打卡, 2=已撤销
    )

    # 关系 - 使用 back_populates 替代 backref
    user = db.relationship('User', foreign_keys=[user_id], back_populates='checkin_records', lazy='selectin')
    solo_user = db.relationship('User', foreign_keys=[solo_user_id], back_populates='solo_checkin_records', lazy='selectin')
    rule = db.relationship('CheckinRule', back_populates='records', lazy='selectin')

    @property
    def status_name(self):
        """获取状态名称"""
        status_mapping = {
            0: 'unchecked',
            1: 'checked',
            2: 'cancelled'
        }
        return status_mapping.get(self.status, 'unknown')

    def __repr__(self):
        return f'<CheckinRecord {self.record_id}: User {self.user_id} at {self.checkin_time}>'


class UserAuditLog(db.Model):
    """用户审计日志表"""
    __tablename__ = 'user_audit_logs'

    log_id = Column(db.Integer, primary_key=True)
    user_id = Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, index=True)
    action = Column(db.String(100), comment='操作类型')
    detail = Column(db.Text, comment='操作详情')
    created_at = Column(db.DateTime, default=datetime.now, index=True)

    # 索引优化
    __table_args__ = (
        db.Index('idx_user_audit_log_user_id', 'user_id'),
        db.Index('idx_user_audit_log_created_at', 'created_at'),
    )

    # 关系 - 使用 back_populates 替代 backref
    user = db.relationship('User', back_populates='audit_logs', lazy='selectin')

    def __repr__(self):
        return f'<UserAuditLog {self.log_id}: User {self.user_id} {self.action}>'


class SupervisionRuleRelation(db.Model):
    """监督规则关系表"""
    __tablename__ = 'supervision_rule_relations'

    relation_id = Column(db.Integer, primary_key=True)
    solo_user_id = Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, index=True)
    supervisor_user_id = Column(db.Integer, db.ForeignKey('users.user_id'), index=True)
    rule_id = Column(db.Integer, db.ForeignKey('checkin_rules.rule_id'), index=True)
    status = Column(db.Integer, default=1, comment='关系状态', index=True)
    created_at = Column(db.DateTime, default=datetime.now, index=True)
    updated_at = Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    invite_token = Column(db.String(64), unique=True)
    invite_expires_at = Column(db.DateTime)

    # 索引优化和约束
    __table_args__ = (
        db.Index('idx_supervision_solo_user_id', 'solo_user_id'),
        db.Index('idx_supervision_supervisor_user_id', 'supervisor_user_id'),
        db.Index('idx_supervision_rule_id', 'rule_id'),
        db.Index('idx_supervision_status', 'status'),
        db.Index('idx_supervision_solo_status', 'solo_user_id', 'status'),
        db.Index('idx_supervision_supervisor_status', 'supervisor_user_id', 'status'),
        db.Index('idx_supervision_rule_status', 'rule_id', 'status'),
        db.Index('idx_supervision_created_at', 'created_at'),
        db.CheckConstraint('status IN (0, 1, 2)', name='ck_supervision_rule_relation_status'),  # 0=停用, 1=待确认, 2=已激活
    )

    # 关系 - 使用 back_populates 替代 backref
    solo_user = db.relationship('User', foreign_keys=[solo_user_id], back_populates='supervised_by_relations', lazy='selectin')
    supervisor_user = db.relationship('User', foreign_keys=[supervisor_user_id], back_populates='supervising_relations', lazy='selectin')
    rule = db.relationship('CheckinRule', back_populates='supervision_relations', lazy='selectin')


class CommunityStaff(db.Model):
    """社区工作人员表"""
    __tablename__ = 'community_staff'

    id = Column(db.Integer, primary_key=True)
    community_id = Column(db.Integer, db.ForeignKey('communities.community_id'), nullable=False, index=True)
    user_id = Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, index=True)
    role = Column(db.String(20), nullable=False, comment='角色')
    scope = Column(db.String(200), comment='负责范围')
    added_at = Column(db.DateTime, default=datetime.now)
    updated_at = Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    removed_at = Column(db.DateTime, nullable=True, comment='移除时间（软删除标记）')

    # 索引优化和约束
    __table_args__ = (
        db.Index('idx_community_staff_community_id', 'community_id'),
        db.Index('idx_community_staff_user_id', 'user_id'),
        db.Index('idx_community_staff_role', 'role'),
        db.Index('idx_community_staff_community_role', 'community_id', 'role'),
        db.Index('idx_community_staff_removed_at', 'removed_at'),
        db.CheckConstraint("role IN ('staff', 'manager')", name='ck_community_staff_role'),
    )

    # 关系 - 使用 back_populates 替代 backref
    community = db.relationship('Community', back_populates='staff_members', lazy='selectin')
    user = db.relationship('User', back_populates='staff_roles', lazy='selectin')


class CommunityCheckinRule(db.Model):
    """社区打卡规则表"""
    __tablename__ = 'community_checkin_rules'

    community_rule_id = Column(Integer, primary_key=True, autoincrement=True)
    community_id = Column(Integer, ForeignKey('communities.community_id'), nullable=False, index=True)
    rule_name = Column(String(100), nullable=False, comment='规则名称')
    icon_url = Column(String(500), comment='图标URL')
    frequency_type = Column(Integer, nullable=False, default=0, comment='频率类型')
    time_slot_type = Column(Integer, nullable=False, default=4, comment='时间段类型')
    custom_time = Column(Time, comment='自定义时间')
    custom_start_date = Column(Date, comment='自定义开始日期')
    custom_end_date = Column(Date, comment='自定义结束日期')
    week_days = Column(Integer, default=127, comment='周天数')
    status = Column(Integer, default=0, comment='规则状态: 0=停用, 1=启用, 2=删除', index=True)
    created_by = Column(Integer, ForeignKey('users.user_id'), nullable=False, comment='创建者', index=True)
    updated_by = Column(Integer, ForeignKey('users.user_id'), comment='最后更新者')
    enabled_at = Column(DateTime, comment='启用时间')
    disabled_at = Column(DateTime, comment='停用时间')
    enabled_by = Column(Integer, ForeignKey('users.user_id'), comment='启用人')
    disabled_by = Column(Integer, ForeignKey('users.user_id'), comment='停用人')
    created_at = Column(DateTime, default=datetime.now, index=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 索引优化和约束
    __table_args__ = (
        db.Index('idx_community_checkin_rule_community_id', 'community_id'),
        db.Index('idx_community_checkin_rule_status', 'status'),
        db.Index('idx_community_checkin_rule_created_by', 'created_by'),
        db.Index('idx_community_checkin_rule_community_status', 'community_id', 'status'),
        db.Index('idx_community_checkin_rule_created_at', 'created_at'),
        db.CheckConstraint('status IN (0, 1, 2)', name='ck_community_checkin_rule_status'),  # 0=停用, 1=启用, 2=删除
    )

    # 关系 - 使用 back_populates 替代 backref
    community = db.relationship('Community', back_populates='community_checkin_rules', lazy='selectin')
    creator = db.relationship('User', foreign_keys=[created_by], lazy='selectin')
    updater = db.relationship('User', foreign_keys=[updated_by], lazy='selectin')
    enabler = db.relationship('User', foreign_keys=[enabled_by], lazy='selectin')
    disabler = db.relationship('User', foreign_keys=[disabled_by], lazy='selectin')
    user_mappings = db.relationship('UserCommunityRule', back_populates='community_rule', lazy='dynamic')

    def to_dict(self):
        """将模型对象转换为字典"""
        result = {
            'community_rule_id': self.community_rule_id,
            'community_id': self.community_id,
            'rule_name': self.rule_name,
            'icon_url': self.icon_url,
            'frequency_type': self.frequency_type,
            'time_slot_type': self.time_slot_type,
            'custom_time': self.custom_time.isoformat() if self.custom_time else None,
            'custom_start_date': self.custom_start_date.isoformat() if self.custom_start_date else None,
            'custom_end_date': self.custom_end_date.isoformat() if self.custom_end_date else None,
            'week_days': self.week_days,
            'status': self.status,
            'created_by': self.created_by,
            'updated_by': self.updated_by,
            'enabled_at': self.enabled_at.isoformat() if self.enabled_at else None,
            'disabled_at': self.disabled_at.isoformat() if self.disabled_at else None,
            'enabled_by': self.enabled_by,
            'disabled_by': self.disabled_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        # 安全地添加关系信息（如果已加载）
        try:
            if self.community:
                result['community_name'] = self.community.name
        except Exception:
            pass  # 关系未加载，忽略

        return result


class CommunityApplication(db.Model):
    """社区申请表"""
    __tablename__ = 'community_applications'

    application_id = Column(db.Integer, primary_key=True)
    user_id = Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, index=True)
    target_community_id = Column(db.Integer, db.ForeignKey('communities.community_id'), nullable=False, index=True)
    status = Column(db.Integer, default=1, nullable=False, comment='申请状态', index=True)
    reason = Column(db.Text, comment='申请理由')
    rejection_reason = Column(db.Text, comment='拒绝理由')
    processed_by = Column(db.Integer, db.ForeignKey('users.user_id'))
    created_at = Column(db.DateTime, default=datetime.now, index=True)
    updated_at = Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 索引优化和约束
    __table_args__ = (
        db.Index('idx_community_application_user_id', 'user_id'),
        db.Index('idx_community_application_target_community_id', 'target_community_id'),
        db.Index('idx_community_application_status', 'status'),
        db.Index('idx_community_application_processed_by', 'processed_by'),
        db.Index('idx_community_application_target_status', 'target_community_id', 'status'),
        db.Index('idx_community_application_created_at', 'created_at'),
        db.CheckConstraint('status IN (1, 2, 3)', name='ck_community_application_status'),  # 1=待审核, 2=已通过, 3=已拒绝
    )

    # 关系 - 使用 back_populates 替代 backref
    user = db.relationship('User', foreign_keys=[user_id], back_populates='community_applications', lazy='selectin')
    processor = db.relationship('User', foreign_keys=[processed_by], back_populates='processed_applications', lazy='selectin')
    target_community = db.relationship('Community', back_populates='applications', lazy='selectin')

    # 兼容性属性
    @property
    def community_id(self):
        """兼容性属性：返回目标社区ID"""
        return self.target_community_id

    @property
    def community(self):
        """兼容性属性：返回目标社区"""
        return self.target_community

    @property
    def applicant_id(self):
        """兼容性属性：返回申请人ID"""
        return self.user_id

    @property
    def applicant(self):
        """兼容性属性：返回申请人"""
        return self.user

    @property
    def message(self):
        """兼容性属性：返回申请理由"""
        return self.reason


class ShareLink(db.Model):
    """分享链接表"""
    __tablename__ = 'share_links'

    link_id = Column(db.Integer, primary_key=True)
    token = Column(db.String(64), unique=True, nullable=False, index=True)
    solo_user_id = Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, index=True)
    rule_id = Column(db.Integer, db.ForeignKey('checkin_rules.rule_id'), nullable=False, index=True)
    expires_at = Column(db.DateTime, nullable=False, index=True)
    created_at = Column(db.DateTime, default=datetime.now, index=True)
    updated_at = Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 索引优化
    __table_args__ = (
        db.Index('idx_share_link_token', 'token'),
        db.Index('idx_share_link_solo_user_id', 'solo_user_id'),
        db.Index('idx_share_link_rule_id', 'rule_id'),
        db.Index('idx_share_link_expires_at', 'expires_at'),
        db.Index('idx_share_link_created_at', 'created_at'),
    )

    # 关系 - 使用 back_populates 替代 backref
    solo_user = db.relationship('User', back_populates='share_links', lazy='selectin')
    rule = db.relationship('CheckinRule', back_populates='share_links', lazy='selectin')


class ShareLinkAccessLog(db.Model):
    """分享链接访问日志表"""
    __tablename__ = 'share_link_access_logs'

    log_id = Column(db.Integer, primary_key=True)
    token = Column(db.String(64), nullable=False, index=True)
    accessed_at = Column(db.DateTime, default=datetime.now, index=True)
    ip_address = Column(db.String(64))
    user_agent = Column(db.String(512))

    # 索引优化
    __table_args__ = (
        db.Index('idx_share_link_access_log_token', 'token'),
        db.Index('idx_share_link_access_log_accessed_at', 'accessed_at'),
    )


class VerificationCode(db.Model):
    """验证码表"""
    __tablename__ = 'verification_codes'

    id = Column(db.Integer, primary_key=True)
    phone_number = Column(db.String(20), nullable=False, index=True)
    purpose = Column(db.String(50), nullable=False, index=True)
    code_hash = Column(db.String(128), nullable=False)
    salt = Column(db.String(32), nullable=False)
    expires_at = Column(db.DateTime, nullable=False, index=True)
    last_sent_at = Column(db.DateTime, nullable=False, index=True)
    is_used = Column(db.Boolean, default=False)
    created_at = Column(db.DateTime, default=datetime.now, index=True)
    updated_at = Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 索引优化
    __table_args__ = (
        db.Index('idx_verification_code_phone_number', 'phone_number'),
        db.Index('idx_verification_code_purpose', 'purpose'),
        db.Index('idx_verification_code_expires_at', 'expires_at'),
        db.Index('idx_verification_code_last_sent_at', 'last_sent_at'),
        db.Index('idx_verification_code_phone_purpose', 'phone_number', 'purpose'),
        db.Index('idx_verification_code_expires_at_status', 'expires_at', 'is_used'),
    )


class Counters(db.Model):
    """计数器表"""
    __tablename__ = 'counters'

    id = Column(db.Integer, primary_key=True)
    count = Column(db.Integer, default=0, comment='计数值')
    created_at = Column(db.DateTime, default=datetime.now)
    updated_at = Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<Counter {self.id}: {self.count}>'


class CommunityEvent(db.Model):
    """社区事件表"""
    __tablename__ = 'community_events'

    event_id = Column(db.Integer, primary_key=True, autoincrement=True)
    community_id = Column(db.Integer, db.ForeignKey('communities.community_id'), nullable=False, index=True)
    title = Column(db.String(200), nullable=False, comment='事件标题')
    description = Column(db.Text, comment='事件描述')
    event_type = Column(db.String(50), nullable=False, default='call_for_help', comment='事件类型')
    status = Column(db.Integer, default=1, comment='事件状态：1-进行中，2-已完成，3-已取消', index=True)
    target_user_id = Column(db.Integer, db.ForeignKey('users.user_id'), comment='目标用户ID', index=True)
    location = Column(db.String(200), comment='事件地点（格式：地址 | 纬度,经度）')
    location_lat = Column(db.Float, comment='纬度')
    location_lon = Column(db.Float, comment='经度')
    created_by = Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, comment='创建者ID', index=True)
    created_at = Column(db.DateTime, default=datetime.now, index=True)
    updated_at = Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    completed_at = Column(db.DateTime, comment='完成时间')
    
    # 新增字段：事件关闭信息
    closed_by = Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True, comment='关闭人ID')
    closed_at = Column(db.DateTime, nullable=True, comment='关闭时间')
    closure_type = Column(db.Integer, nullable=True, comment='关闭类型：1-用户关闭，2-工作人员关闭')
    closure_reason = Column(db.String(500), nullable=True, comment='关闭原因（10-500字符）')

    # 索引优化和约束
    __table_args__ = (
        db.Index('idx_community_event_community_id', 'community_id'),
        db.Index('idx_community_event_event_type', 'event_type'),
        db.Index('idx_community_event_status', 'status'),
        db.Index('idx_community_event_target_user_id', 'target_user_id'),
        db.Index('idx_community_event_created_by', 'created_by'),
        db.Index('idx_community_event_community_status', 'community_id', 'status'),
        db.Index('idx_community_event_type_status', 'event_type', 'status'),
        db.Index('idx_community_event_created_at', 'created_at'),
        db.Index('idx_community_event_closed_by', 'closed_by'),
        db.Index('idx_community_event_closed_at', 'closed_at'),
        db.Index('idx_community_event_closure_type', 'closure_type'),
        db.CheckConstraint("event_type IN ('call_for_help', 'supporting')", name='ck_community_event_type'),
        db.CheckConstraint('status IN (1, 2, 3)', name='ck_community_event_status'),  # 1=进行中, 2=已完成, 3=已取消
    )

    # 关系 - 使用 back_populates 替代 backref
    community = db.relationship('Community', back_populates='events', lazy='selectin')
    creator = db.relationship('User', foreign_keys=[created_by], back_populates='created_events', lazy='selectin')
    target_user = db.relationship('User', foreign_keys=[target_user_id], back_populates='targeted_events', lazy='selectin')
    supports = db.relationship('EventMessage', back_populates='event', cascade='all, delete-orphan', lazy='selectin')
    closer = db.relationship('User', foreign_keys=[closed_by], backref='closed_events', lazy='selectin')

    # 事件类型映射
    EVENT_TYPE_MAPPING = {
        'call_for_help': '求助',
        'supporting': '应援'
    }

    # 状态映射
    STATUS_MAPPING = {
        1: '进行中',
        2: '已完成',
        3: '已取消'
    }

    # 关闭类型映射
    CLOSURE_TYPE_MAPPING = {
        1: '用户关闭',
        2: '工作人员关闭'
    }

    @property
    def event_type_label(self):
        """获取事件类型标签"""
        return self.EVENT_TYPE_MAPPING.get(self.event_type, '未知')

    @property
    def status_label(self):
        """获取状态标签"""
        return self.STATUS_MAPPING.get(self.status, '未知')

    @property
    def closure_type_label(self):
        """获取关闭类型标签"""
        return self.CLOSURE_TYPE_MAPPING.get(self.closure_type, '未知')

    def to_dict(self):
        """将模型对象转换为字典"""
        result = {
            'event_id': self.event_id,
            'community_id': self.community_id,
            'title': self.title,
            'description': self.description,
            'event_type': self.event_type,
            'event_type_label': self.event_type_label,
            'status': self.status,
            'status_label': self.status_label,
            'target_user_id': self.target_user_id,
            'location': self.location,
            'location_lat': self.location_lat,
            'location_lon': self.location_lon,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'closed_by': self.closed_by,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'closure_type': self.closure_type,
            'closure_type_label': self.closure_type_label if self.closure_type else None,
            'closure_reason': self.closure_reason,
            'support_count': len([s for s in self.supports if s.status == 1])
        }

        return result


class EventMessage(db.Model):
    """事件消息记录表"""
    __tablename__ = 'event_messages'

    message_id = Column(db.Integer, primary_key=True, autoincrement=True)
    event_id = Column(db.Integer, db.ForeignKey('community_events.event_id'), nullable=False, index=True)
    sender_id = Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, index=True)
    message_content = Column(db.Text, comment='消息内容')
    status = Column(db.Integer, default=1, comment='消息状态：1-有效，2-已取消', index=True)
    created_at = Column(db.DateTime, default=datetime.now, index=True)
    updated_at = Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 新增字段：支持多媒体消息和回应标签
    message_type = Column(db.String(20), default='text', comment='消息类型：text/voice/image')
    media_url = Column(db.String(500), comment='媒体文件URL（语音或图片）')
    media_duration = Column(db.Integer, comment='语音时长（秒）')
    message_tags = Column(db.JSON, comment='回应标签数组，如["已电话联系", "正在前往"]')

    # 索引优化和约束
    __table_args__ = (
        db.Index('idx_event_support_event_id', 'event_id'),
        db.Index('idx_event_support_sender_id', 'sender_id'),
        db.Index('idx_event_support_status', 'status'),
        db.Index('idx_event_support_event_status', 'event_id', 'status'),
        db.Index('idx_event_support_created_at', 'created_at'),
        db.CheckConstraint('status IN (1, 2)', name='ck_event_support_status'),  # 1=有效, 2=已取消
        db.CheckConstraint("message_type IN ('text', 'voice', 'image')", name='ck_event_support_message_type'),
    )

    # 关系 - 使用 back_populates 替代 backref
    sender = db.relationship('User', back_populates='supports', lazy='selectin')
    event = db.relationship('CommunityEvent', back_populates='supports', lazy='selectin')

    # 状态映射
    STATUS_MAPPING = {
        1: '有效',
        2: '已取消'
    }

    # 消息类型映射
    MESSAGE_TYPE_MAPPING = {
        'text': '文字',
        'voice': '语音',
        'image': '图片'
    }

    @property
    def status_label(self):
        """获取状态标签"""
        return self.STATUS_MAPPING.get(self.status, '未知')

    @property
    def message_type_label(self):
        """获取消息类型标签"""
        return self.MESSAGE_TYPE_MAPPING.get(self.message_type, '未知')

    def to_dict(self):
        """将模型对象转换为字典"""
        result = {
            'message_id': self.message_id,
            'event_id': self.event_id,
            'sender_id': self.sender_id,
            'message_content': self.message_content,
            'status': self.status,
            'status_label': self.status_label,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'message_type': self.message_type,
            'message_type_label': self.message_type_label,
            'media_url': self.media_url,
            'media_duration': self.media_duration,
            'message_tags': self.message_tags or []
        }

        return result


class UserCommunityRule(db.Model):
    """用户社区规则映射表 - Flask-SQLAlchemy版本"""
    __tablename__ = 'user_community_rules'

    mapping_id = Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    community_rule_id = Column(db.Integer, db.ForeignKey('community_checkin_rules.community_rule_id'), nullable=False)
    is_active = Column(db.Boolean, default=True, comment='是否对该用户生效')
    created_at = Column(db.DateTime, default=datetime.now)

    # 唯一约束和索引优化
    __table_args__ = (
        db.UniqueConstraint('user_id', 'community_rule_id', name='uq_user_community_rule'),
        # 为常用查询添加索引
        db.Index('idx_user_community_rules_user_id', 'user_id'),
        db.Index('idx_user_community_rules_community_rule_id', 'community_rule_id'),
        db.Index('idx_user_community_rules_user_active', 'user_id', 'is_active'),
    )

    # 关系 - 使用 back_populates 替代 backref
    user = db.relationship('User', back_populates='user_community_rules', lazy='selectin')
    community_rule = db.relationship('CommunityCheckinRule', back_populates='user_mappings', lazy='selectin')

    def __repr__(self):
        return f'<UserCommunityRule {self.mapping_id}: User{self.user_id}-Rule{self.community_rule_id}>'

    def to_dict(self):
        """将模型对象转换为字典"""
        return {
            'mapping_id': self.mapping_id,
            'user_id': self.user_id,
            'community_rule_id': self.community_rule_id,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# 导出 Base 供 Alembic 使用
Base = db.Model