"""
Flask-SQLAlchemy模型定义
从纯SQLAlchemy迁移到Flask-SQLAlchemy
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Date, Time, Float, CheckConstraint, UniqueConstraint, Index

# 创建SQLAlchemy实例
db = SQLAlchemy()

class User(db.Model):
    """用户表 - Flask-SQLAlchemy版本"""
    __tablename__ = 'users'

    user_id = Column(db.Integer, primary_key=True)
    wechat_openid = Column(db.String(128), unique=True, nullable=True, comment='微信OpenID')
    phone_number = Column(db.String(20), comment='手机号码')
    phone_hash = Column(db.String(64), unique=True, nullable=True, comment='手机号哈希')
    nickname = Column(db.String(100), comment='用户昵称')
    avatar_url = Column(db.String(500), comment='用户头像URL')
    name = Column(db.String(100), comment='真实姓名')
    work_id = Column(db.String(50), comment='工号或身份证号')
    password_hash = Column(db.String(128), comment='密码哈希')
    password_salt = Column(db.String(32), comment='密码盐')
    role = Column(db.Integer, nullable=False, comment='用户角色')
    status = Column(db.Integer, default=1, comment='用户状态')
    verification_status = Column(db.Integer, default=0, comment='验证状态')
    verification_materials = Column(db.Text, comment='验证材料')
    _is_community_worker = Column('is_community_worker', Boolean, default=False)
    community_id = Column(db.Integer, db.ForeignKey('communities.community_id', use_alter=True))
    community_joined_at = Column(db.DateTime, comment='加入当前社区的时间')
    refresh_token = Column(db.String(128), comment='刷新令牌')
    refresh_token_expire = Column(db.DateTime, comment='刷新令牌过期时间')
    created_at = Column(db.DateTime, default=datetime.now)
    updated_at = Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    community = db.relationship('Community', foreign_keys=[community_id], backref='users')

    # 角色映射
    ROLE_MAPPING = {
        1: '普通用户',
        2: '社区专员',
        3: '社区主管',
        4: '超级系统管理员'
    }

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
        """获取角色名称"""
        return self.ROLE_MAPPING.get(self.role, '未知角色')

    @property
    def status_name(self):
        """获取状态名称"""
        return self.STATUS_MAPPING.get(self.status, '未知状态')


class Community(db.Model):
    """社区表"""
    __tablename__ = 'communities'

    community_id = Column(db.Integer, primary_key=True)
    name = Column(db.String(100), nullable=False, unique=True, comment='社区名称')
    description = Column(db.Text, comment='社区描述')
    creator_user_id = Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True, comment='创建人ID')
    status = Column(db.Integer, default=1, nullable=False, comment='社区状态')
    settings = Column(db.Text, comment='社区设置（JSON）')
    location = Column(db.String(200), comment='地理位置')
    location_lat = Column(db.Float, comment='纬度')
    location_lon = Column(db.Float, comment='经度')
    is_default = Column(db.Boolean, default=False, nullable=False, comment='是否默认社区')
    is_blackhouse = Column(db.Boolean, default=False, nullable=False, comment='是否黑屋社区')
    created_at = Column(db.DateTime, default=datetime.now)
    updated_at = Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    creator = db.relationship('User', foreign_keys=[creator_user_id], backref='created_communities')
    # 注意：users backref 与 User 模型中的 community 关系冲突，所以不在这里定义

    # 状态映射
    STATUS_MAPPING = {
        1: 'enabled',
        2: 'disabled'
    }

    @property
    def status_name(self):
        """获取状态名称"""
        return self.STATUS_MAPPING.get(self.status, 'unknown')

    def __repr__(self):
        return f'<Community {self.community_id}: {self.name}>'


class CheckinRule(db.Model):
    """打卡规则表"""
    __tablename__ = 'checkin_rules'

    rule_id = Column(db.Integer, primary_key=True)
    user_id = Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    community_id = Column(db.Integer, db.ForeignKey('communities.community_id'), nullable=False)
    rule_type = Column(db.String(50), nullable=False, comment='规则类型')
    rule_content = Column(db.Text, comment='规则内容')
    is_active = Column(db.Boolean, default=True, comment='是否激活')
    created_at = Column(db.DateTime, default=datetime.now)
    updated_at = Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    user = db.relationship('User', backref='checkin_rules')
    community = db.relationship('Community', backref='checkin_rules')

    def __repr__(self):
        return f'<CheckinRule {self.rule_id}: {self.rule_type}>'


class CheckinRecord(db.Model):
    """打卡记录表"""
    __tablename__ = 'checkin_records'

    record_id = Column(db.Integer, primary_key=True)
    user_id = Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    rule_id = Column(db.Integer, db.ForeignKey('checkin_rules.rule_id'), nullable=False)
    checkin_time = Column(db.DateTime, default=datetime.now, comment='打卡时间')
    checkin_type = Column(db.String(50), comment='打卡类型')
    content = Column(db.Text, comment='打卡内容')
    created_at = Column(db.DateTime, default=datetime.now)

    # 关系
    user = db.relationship('User', backref='checkin_records')
    rule = db.relationship('CheckinRule', backref='records')

    def __repr__(self):
        return f'<CheckinRecord {self.record_id}: User {self.user_id} at {self.checkin_time}>'


class UserAuditLog(db.Model):
    """用户审计日志表"""
    __tablename__ = 'user_audit_logs'

    log_id = Column(db.Integer, primary_key=True)
    user_id = Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    action = Column(db.String(100), comment='操作类型')
    detail = Column(db.Text, comment='操作详情')
    created_at = Column(db.DateTime, default=datetime.now)

    # 关系
    user = db.relationship('User', backref='audit_logs')

    def __repr__(self):
        return f'<UserAuditLog {self.log_id}: User {self.user_id} {self.action}>'


class SupervisionRuleRelation(db.Model):
    """监督规则关系表"""
    __tablename__ = 'supervision_rule_relations'

    relation_id = Column(db.Integer, primary_key=True)
    solo_user_id = Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    supervisor_user_id = Column(db.Integer, db.ForeignKey('users.user_id'))
    rule_id = Column(db.Integer, db.ForeignKey('checkin_rules.rule_id'))
    status = Column(db.Integer, default=1, comment='关系状态')
    created_at = Column(db.DateTime, default=datetime.now)
    updated_at = Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    invite_token = Column(db.String(64), unique=True)
    invite_expires_at = Column(db.DateTime)

    # 关系
    solo_user = db.relationship('User', foreign_keys=[solo_user_id], backref='supervised_by_relations')
    supervisor_user = db.relationship('User', foreign_keys=[supervisor_user_id], backref='supervising_relations')
    rule = db.relationship('CheckinRule', backref='supervision_relations')


class CommunityStaff(db.Model):
    """社区工作人员表"""
    __tablename__ = 'community_staff'

    id = Column(db.Integer, primary_key=True)
    community_id = Column(db.Integer, db.ForeignKey('communities.community_id'), nullable=False)
    user_id = Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    role = Column(db.String(20), nullable=False, comment='角色')
    scope = Column(db.String(200), comment='负责范围')
    added_at = Column(db.DateTime, default=datetime.now)
    updated_at = Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    community = db.relationship('Community', backref='staff_members')
    user = db.relationship('User', backref='staff_roles')

class CommunityCheckinRule(db.Model):
    """社区打卡规则表"""
    __tablename__ = 'community_checkin_rules'

    community_rule_id = Column(Integer, primary_key=True, autoincrement=True)
    community_id = Column(Integer, ForeignKey('communities.community_id'), nullable=False)
    rule_name = Column(String(100), nullable=False, comment='规则名称')
    icon_url = Column(String(500), comment='图标URL')
    frequency_type = Column(Integer, nullable=False, default=0, comment='频率类型')
    time_slot_type = Column(Integer, nullable=False, default=4, comment='时间段类型')
    custom_time = Column(Time, comment='自定义时间')
    custom_start_date = Column(Date, comment='自定义开始日期')
    custom_end_date = Column(Date, comment='自定义结束日期')
    week_days = Column(Integer, default=127, comment='周天数')
    status = Column(Integer, default=0, comment='规则状态: 0=停用, 1=启用, 2=删除')
    created_by = Column(Integer, ForeignKey('users.user_id'), nullable=False, comment='创建者')
    updated_by = Column(Integer, ForeignKey('users.user_id'), comment='最后更新者')
    enabled_at = Column(DateTime, comment='启用时间')
    disabled_at = Column(DateTime, comment='停用时间')
    enabled_by = Column(Integer, ForeignKey('users.user_id'), comment='启用人')
    disabled_by = Column(Integer, ForeignKey('users.user_id'), comment='停用人')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    community = db.relationship('Community', backref='community_checkin_rules')
    creator = db.relationship('User', foreign_keys=[created_by])
    updater = db.relationship('User', foreign_keys=[updated_by])
    enabler = db.relationship('User', foreign_keys=[enabled_by])
    disabler = db.relationship('User', foreign_keys=[disabled_by])

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

        try:
            if self.creator:
                result['created_by_name'] = self.creator.nickname or self.creator.phone
        except Exception:
            pass

        try:
            if self.updater:
                result['updated_by_name'] = self.updater.nickname or self.updater.phone
        except Exception:
            pass

        try:
            if self.enabler:
                result['enabled_by_name'] = self.enabler.nickname or self.enabler.phone
        except Exception:
            pass

        try:
            if self.disabler:
                result['disabled_by_name'] = self.disabler.nickname or self.disabler.phone
        except Exception:
            pass

        return result

class CommunityApplication(db.Model):
    """社区申请表"""
    __tablename__ = 'community_applications'

    application_id = Column(db.Integer, primary_key=True)
    user_id = Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    target_community_id = Column(db.Integer, db.ForeignKey('communities.community_id'), nullable=False)
    status = Column(db.Integer, default=1, nullable=False)
    reason = Column(db.Text, comment='申请理由')
    rejection_reason = Column(db.Text, comment='拒绝理由')
    processed_by = Column(db.Integer, db.ForeignKey('users.user_id'))
    created_at = Column(db.DateTime, default=datetime.now)
    updated_at = Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    user = db.relationship('User', foreign_keys=[user_id], backref='community_applications')
    processor = db.relationship('User', foreign_keys=[processed_by], backref='processed_applications')
    target_community = db.relationship('Community', backref='applications')


class ShareLink(db.Model):
    """分享链接表"""
    __tablename__ = 'share_links'

    link_id = Column(db.Integer, primary_key=True)
    token = Column(db.String(64), unique=True, nullable=False)
    solo_user_id = Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    rule_id = Column(db.Integer, db.ForeignKey('checkin_rules.rule_id'), nullable=False)
    expires_at = Column(db.DateTime, nullable=False)
    created_at = Column(db.DateTime, default=datetime.now)
    updated_at = Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    solo_user = db.relationship('User', backref='share_links')
    rule = db.relationship('CheckinRule', backref='share_links')


class ShareLinkAccessLog(db.Model):
    """分享链接访问日志表"""
    __tablename__ = 'share_link_access_logs'

    log_id = Column(db.Integer, primary_key=True)
    token = Column(db.String(64), nullable=False)
    accessed_at = Column(db.DateTime, default=datetime.now)
    ip_address = Column(db.String(64))
    user_agent = Column(db.String(512))


class VerificationCode(db.Model):
    """验证码表"""
    __tablename__ = 'verification_codes'

    id = Column(db.Integer, primary_key=True)
    phone_number = Column(db.String(20), nullable=False)
    purpose = Column(db.String(50), nullable=False)
    code_hash = Column(db.String(128), nullable=False)
    salt = Column(db.String(32), nullable=False)
    expires_at = Column(db.DateTime, nullable=False)
    last_sent_at = Column(db.DateTime, nullable=False)
    is_used = Column(db.Boolean, default=False)
    created_at = Column(db.DateTime, default=datetime.now)
    updated_at = Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class Counters(db.Model):
    """计数器表"""
    __tablename__ = 'counters'

    id = Column(db.Integer, primary_key=True)
    count = Column(db.Integer, default=0, comment='计数值')
    created_at = Column(db.DateTime, default=datetime.now)
    updated_at = Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<Counter {self.id}: {self.count}>'