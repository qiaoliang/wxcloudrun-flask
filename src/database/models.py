"""
纯SQLAlchemy模型定义
完全独立于Flask，使用标准的SQLAlchemy ORM
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Date, Time, Float
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from .query_mixin import QueryMixin

# 创建基础模型类
Base = declarative_base()


class User(Base, QueryMixin):
    """用户表"""
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    wechat_openid = Column(String(128),unique=True, nullable=True, comment='微信OpenID')
    phone_number = Column(String(20), comment='手机号码')
    phone_hash = Column(String(64), unique=True, nullable=True, comment='手机号哈希')
    nickname = Column(String(100), comment='用户昵称')
    avatar_url = Column(String(500), comment='用户头像URL')
    name = Column(String(100), comment='真实姓名')
    work_id = Column(String(50), comment='工号或身份证号')
    password_hash = Column(String(128), comment='密码哈希')
    password_salt = Column(String(32), comment='密码盐')
    role = Column(Integer, nullable=False, comment='用户角色')
    status = Column(Integer, default=1, comment='用户状态')
    verification_status = Column(Integer, default=0, comment='验证状态')
    verification_materials = Column(Text, comment='验证材料')
    _is_community_worker = Column('is_community_worker', Boolean, default=False)
    community_id = Column(Integer, ForeignKey('communities.community_id', use_alter=True))
    refresh_token = Column(String(128), comment='刷新令牌')
    refresh_token_expire = Column(DateTime, comment='刷新令牌过期时间')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    community = relationship('Community', foreign_keys=[community_id], backref='users')

    # 角色映射
    ROLE_MAPPING = {
        1: '普通用户',  # 普通用户
        2: '社区专员',  # 社区专员
        3: '社区主管',     # 社区主管
        4: '超级系统管理员'      # 超级系统管理员
    }

    # 状态映射
    STATUS_MAPPING = {
        1: 'enabled',
        2: 'disabled'
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


class Community(Base, QueryMixin):
    """社区表"""
    __tablename__ = 'communities'

    community_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, comment='社区名称')
    description = Column(Text, comment='社区描述')
    creator_user_id = Column(Integer, ForeignKey('users.user_id', use_alter=True), nullable=True, comment='创建人ID')
    status = Column(Integer, default=1, nullable=False, comment='社区状态')
    settings = Column(Text, comment='社区设置（JSON）')
    location = Column(String(200), comment='地理位置')
    location_lat = Column(Float, comment='纬度')
    location_lon = Column(Float, comment='经度')
    is_default = Column(Boolean, default=False, nullable=False, comment='是否默认社区')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    creator = relationship('User', foreign_keys=[creator_user_id], backref='created_communities')

    # 状态映射
    STATUS_MAPPING = {
        1: 'enabled',
        2: 'disabled'
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


class CheckinRule(Base, QueryMixin):
    """打卡规则表"""
    __tablename__ = 'checkin_rules'

    rule_id = Column(Integer, primary_key=True, autoincrement=True)
    solo_user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    rule_name = Column(String(100), nullable=False, comment='规则名称')
    icon_url = Column(String(500), comment='图标URL')
    frequency_type = Column(Integer, nullable=False, default=0, comment='频率类型')
    time_slot_type = Column(Integer, nullable=False, default=4, comment='时间段类型')
    custom_time = Column(Time, comment='自定义时间')
    custom_start_date = Column(Date, comment='自定义开始日期')
    custom_end_date = Column(Date, comment='自定义结束日期')
    week_days = Column(Integer, default=127, comment='周天数')
    status = Column(Integer, default=1, comment='规则状态')
    deleted_at = Column(DateTime, comment='删除时间')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    user = relationship('User', backref='checkin_rules')


class CheckinRecord(Base, QueryMixin):
    """打卡记录表"""
    __tablename__ = 'checkin_records'

    record_id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(Integer, ForeignKey('checkin_rules.rule_id'), nullable=False)
    solo_user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    checkin_time = Column(DateTime, comment='打卡时间')
    status = Column(Integer, default=0, comment='状态')
    planned_time = Column(DateTime, nullable=False, comment='计划时间')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    rule = relationship('CheckinRule', backref='checkin_records')
    user = relationship('User', backref='checkin_records')


class SupervisionRuleRelation(Base, QueryMixin):
    """监督规则关系表"""
    __tablename__ = 'supervision_rule_relations'

    relation_id = Column(Integer, primary_key=True, autoincrement=True)
    solo_user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    supervisor_user_id = Column(Integer, ForeignKey('users.user_id'))
    rule_id = Column(Integer, ForeignKey('checkin_rules.rule_id'))
    status = Column(Integer, default=1, comment='关系状态')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    invite_token = Column(String(64), unique=True)
    invite_expires_at = Column(DateTime)

    # 关系
    solo_user = relationship('User', foreign_keys=[solo_user_id], backref='supervised_by_relations')
    supervisor_user = relationship('User', foreign_keys=[supervisor_user_id], backref='supervising_relations')
    rule = relationship('CheckinRule', backref='supervision_relations')


class CommunityStaff(Base, QueryMixin):
    """社区工作人员表"""
    __tablename__ = 'community_staff'

    id = Column(Integer, primary_key=True, autoincrement=True)
    community_id = Column(Integer, ForeignKey('communities.community_id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    role = Column(String(20), nullable=False, comment='角色')
    scope = Column(String(200), comment='负责范围')
    added_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    community = relationship('Community', backref='staff_members')
    user = relationship('User', backref='staff_roles')


class CommunityMember(Base, QueryMixin):
    """社区成员表"""
    __tablename__ = 'community_members'

    id = Column(Integer, primary_key=True, autoincrement=True)
    community_id = Column(Integer, ForeignKey('communities.community_id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    joined_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    community = relationship('Community', backref='members')
    user = relationship('User', backref='community_memberships')


class CommunityApplication(Base, QueryMixin):
    """社区申请表"""
    __tablename__ = 'community_applications'

    application_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    target_community_id = Column(Integer, ForeignKey('communities.community_id'), nullable=False)
    status = Column(Integer, default=1, nullable=False)
    reason = Column(Text, comment='申请理由')
    rejection_reason = Column(Text, comment='拒绝理由')
    processed_by = Column(Integer, ForeignKey('users.user_id'))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    user = relationship('User', foreign_keys=[user_id], backref='community_applications')
    processor = relationship('User', foreign_keys=[processed_by], backref='processed_applications')
    target_community = relationship('Community', backref='applications')


class ShareLink(Base, QueryMixin):
    """分享链接表"""
    __tablename__ = 'share_links'

    link_id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String(64), unique=True, nullable=False)
    solo_user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    rule_id = Column(Integer, ForeignKey('checkin_rules.rule_id'), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    solo_user = relationship('User', backref='share_links')
    rule = relationship('CheckinRule', backref='share_links')


class ShareLinkAccessLog(Base, QueryMixin):
    """分享链接访问日志表"""
    __tablename__ = 'share_link_access_logs'

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String(64), nullable=False)
    accessed_at = Column(DateTime, default=datetime.now)
    ip_address = Column(String(64))
    user_agent = Column(String(512))
    supervisor_user_id = Column(Integer)

    # 关系
    # supervisor_user = relationship('User', backref='access_logs')


class VerificationCode(Base, QueryMixin):
    """验证码表"""
    __tablename__ = 'verification_codes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone_number = Column(String(20), nullable=False)
    purpose = Column(String(50), nullable=False)
    code_hash = Column(String(128), nullable=False)
    salt = Column(String(32), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    last_sent_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class UserAuditLog(Base, QueryMixin):
    """用户审计日志表"""
    __tablename__ = 'user_audit_logs'

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    action = Column(String(100), nullable=False)
    detail = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

    # 关系
    # user = relationship('User', backref='audit_logs')


class Counters(Base, QueryMixin):
    """计数器表"""
    __tablename__ = 'Counters'

    id = Column(Integer, primary_key=True)
    count = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


# 导出所有模型
__all__ = [
    'Base', 'User', 'Community', 'CheckinRule', 'CheckinRecord',
    'SupervisionRuleRelation', 'CommunityStaff', 'CommunityMember',
    'CommunityApplication', 'ShareLink', 'ShareLinkAccessLog',
    'VerificationCode', 'UserAuditLog', 'Counters'
]