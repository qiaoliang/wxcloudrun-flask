from datetime import datetime

from wxcloudrun import db


# 计数表
class Counters(db.Model):
    # 设置结构体表格名称
    __tablename__ = 'Counters'

    # 设定结构体对应表格的字段
    id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer, default=1)
    created_at = db.Column('createdAt', db.TIMESTAMP, nullable=False, default=datetime.now)
    updated_at = db.Column('updatedAt', db.TIMESTAMP, nullable=False, default=datetime.now)


# 用户表
class User(db.Model):
    # 设置结构体表格名称
    __tablename__ = 'users'

    # 设定结构体对应表格的字段
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    wechat_openid = db.Column(db.String(128), unique=True, nullable=False, comment='微信OpenID，唯一标识用户')
    phone_number = db.Column(db.String(20), unique=True, comment='手机号码，可用于登录和联系')
    nickname = db.Column(db.String(100), comment='用户昵称')
    avatar_url = db.Column(db.String(500), comment='用户头像URL')
    role = db.Column(db.Enum('solo', 'supervisor', 'community', name='user_role'), nullable=False, comment='用户角色：独居者/监护人/社区工作人员')
    community_id = db.Column(db.Integer, comment='所属社区ID，仅社区工作人员需要')
    status = db.Column(db.Enum('active', 'disabled', name='user_status'), default='active', comment='用户状态：正常/禁用')
    created_at = db.Column(db.TIMESTAMP, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.TIMESTAMP, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    # 索引
    __table_args__ = (
        db.Index('idx_openid', 'wechat_openid'),  # 微信OpenID索引，支持快速登录查询
        db.Index('idx_phone', 'phone_number'),    # 手机号索引，支持手机号登录
        db.Index('idx_role', 'role'),             # 角色索引，支持按角色查询
    )
