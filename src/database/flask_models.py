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
    address = Column(db.String(200), comment='社区地址')
    created_at = Column(db.DateTime, default=datetime.now)
    updated_at = Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    status = Column(db.Integer, default=1, comment='社区状态')

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


class Counters(db.Model):
    """计数器表"""
    __tablename__ = 'counters'

    id = Column(db.Integer, primary_key=True)
    count = Column(db.Integer, default=0, comment='计数值')
    created_at = Column(db.DateTime, default=datetime.now)
    updated_at = Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<Counter {self.id}: {self.count}>'