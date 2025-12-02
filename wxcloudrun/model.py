from datetime import datetime
import os

from sqlalchemy import Column, Integer, String, DateTime, Text, text, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
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
    wechat_openid = db.Column(db.String(128), unique=True, nullable=False, comment='微信OpenID，唯一标识用户')
    phone_number = db.Column(db.String(20), unique=True, comment='手机号码，可用于登录和联系')
    nickname = db.Column(db.String(100), comment='用户昵称')
    avatar_url = db.Column(db.String(500), comment='用户头像URL')
    name = db.Column(db.String(100), comment='真实姓名')
    work_id = db.Column(db.String(50), comment='工号或身份证号')
    
    # 用户权限字段，支持多身份组合
    # 基础身份标识
    is_solo_user = db.Column(db.Boolean, default=True, comment='是否为独居者（有打卡规则和记录）')
    is_supervisor = db.Column(db.Boolean, default=False, comment='是否为监护人（有关联的监护关系）')
    is_community_worker = db.Column(db.Boolean, default=False, comment='是否为社区工作人员（需要身份验证）')
    
    # 兼容性字段，暂时保留，后续可移除
    role = db.Column(db.Integer, default=1, comment='兼容性字段：1-独居者/2-监护人/3-社区工作人员')
    
    # 状态: 1-正常, 2-禁用
    status = db.Column(db.Integer, default=1, comment='用户状态：1-正常/2-禁用')
    
    # 验证状态: 0-未申请, 1-待审核, 2-已通过, 3-已拒绝
    verification_status = db.Column(db.Integer, default=0, comment='验证状态：0-未申请/1-待审核/2-已通过/3-已拒绝')
    verification_materials = db.Column(db.Text, comment='验证材料URL')
    
    community_id = db.Column(db.Integer, comment='所属社区ID，仅社区工作人员需要')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

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
        """获取角色名称（兼容性方法）"""
        # 优先返回主要角色，如果有多个身份，优先返回独居者
        if self.is_solo_user:
            return 'solo'
        elif self.is_supervisor:
            return 'supervisor'
        elif self.is_community_worker:
            return 'community'
        return self.ROLE_MAPPING.get(self.role, 'unknown')

    @property
    def status_name(self):
        """获取状态名称"""
        return self.STATUS_MAPPING.get(self.status, 'unknown')

    @property
    def has_supervisor_features(self):
        """是否有监护人功能权限"""
        return self.is_supervisor or self.is_solo_user

    @property
    def has_community_features(self):
        """是否有社区功能权限"""
        return self.is_community_worker and self.verification_status == 2

    @property
    def permissions(self):
        """获取用户权限列表"""
        permissions = []
        if self.is_solo_user:
            permissions.append('solo_user')
        if self.is_supervisor:
            permissions.append('supervisor')
        if self.is_community_worker and self.verification_status == 2:
            permissions.append('community_worker')
        return permissions

    def has_permission(self, permission):
        """检查是否有特定权限"""
        return permission in self.permissions

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
    solo_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, comment='独居者用户ID')
    rule_name = db.Column(db.String(100), nullable=False, comment='打卡规则名称，如：起床打卡、早餐打卡等')
    icon_url = db.Column(db.String(500), comment='打卡事项图标URL')
    
    # 频率类型: 0-每天, 1-每周, 2-工作日, 3-自定义
    frequency_type = db.Column(db.Integer, nullable=False, default=0, comment='打卡频率类型：0-每天/1-每周/2-工作日/3-自定义')
    
    # 时间段类型: 1-上午, 2-下午, 3-晚上, 4-自定义时间
    time_slot_type = db.Column(db.Integer, nullable=False, default=4, comment='时间段类型：1-上午/2-下午/3-晚上/4-自定义时间')
    
    # 自定义时间（当time_slot_type为4时使用）
    custom_time = db.Column(db.Time, comment='自定义打卡时间')
    
    # 一周中的天（当frequency_type为1时使用，使用位掩码表示周几）
    week_days = db.Column(db.Integer, default=127, comment='一周中的天（位掩码表示）：默认127表示周一到周日')
    
    # 规则状态：1-启用, 0-禁用
    status = db.Column(db.Integer, default=1, comment='规则状态：1-启用/0-禁用')
    
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    # 关联用户
    user = db.relationship('User', backref=db.backref('checkin_rules', lazy=True))

    # 索引和表选项
    __table_args__ = (
        db.Index('idx_rule_solo_user', 'solo_user_id'),  # 用户ID索引
        {
            'mysql_charset': 'utf8mb4',
            'mysql_collate': 'utf8mb4_unicode_ci'
        }
    )


# 打卡记录表
class CheckinRecord(db.Model):
    # 设置结构体表格名称
    __tablename__ = 'checkin_records'

    # 设定结构体对应表格的字段
    record_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rule_id = db.Column(db.Integer, db.ForeignKey('checkin_rules.rule_id'), nullable=False, comment='打卡规则ID')
    solo_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, comment='独居者用户ID')
    checkin_time = db.Column(db.DateTime, comment='实际打卡时间')
    
    # 状态: 1-checked(已打卡), 0-missed(未打卡), 2-revoked(已撤销)
    status = db.Column(db.Integer, default=0, comment='状态：0-未打卡/1-已打卡/2-已撤销')
    
    planned_time = db.Column(db.DateTime, nullable=False, comment='计划打卡时间')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    # 关联规则和用户
    rule = db.relationship('CheckinRule', backref=db.backref('checkin_records', lazy=True))
    user = db.relationship('User', backref=db.backref('checkin_records', lazy=True))

    # 索引和表选项
    __table_args__ = (
        db.Index('idx_record_rule', 'rule_id'),  # 规则ID索引
        db.Index('idx_record_solo_user', 'solo_user_id'),  # 用户ID索引
        db.Index('idx_planned_time', 'planned_time'),  # 计划时间索引
        {
            'mysql_charset': 'utf8mb4',
            'mysql_collate': 'utf8mb4_unicode_ci'
        }
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


# 规则监护关系表
class RuleSupervision(db.Model):
    __tablename__ = 'rule_supervisions'
    
    # 主键
    rule_supervision_id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='监护关系ID')
    
    # 关联字段
    rule_id = db.Column(db.Integer, db.ForeignKey('checkin_rules.rule_id'), nullable=False, comment='打卡规则ID')
    solo_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, comment='独居者用户ID')
    supervisor_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, comment='监护人用户ID')
    
    # 状态管理
    status = db.Column(db.Integer, default=0, comment='监护关系状态：0-待确认/1-已确认/2-已拒绝/3-已取消')
    
    # 邀请信息
    invitation_message = db.Column(db.Text, comment='邀请消息')
    invited_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, comment='邀请人ID')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    responded_at = db.Column(db.DateTime, comment='响应时间')
    
    # 关联关系
    rule = db.relationship('CheckinRule', backref=db.backref('supervisions', lazy=True))
    solo_user = db.relationship('User', foreign_keys=[solo_user_id], backref=db.backref('solo_supervisions', lazy=True))
    supervisor_user = db.relationship('User', foreign_keys=[supervisor_user_id], backref=db.backref('supervisor_rules', lazy=True))
    invited_by = db.relationship('User', foreign_keys=[invited_by_user_id])
    
    # 索引和表选项
    __table_args__ = (
        db.Index('idx_rule_supervision', 'rule_id', 'supervisor_user_id'),
        db.Index('idx_supervisor_invitations', 'supervisor_user_id', 'status'),
        db.Index('idx_solo_supervisions', 'solo_user_id', 'status'),
        {
            'mysql_charset': 'utf8mb4',
            'mysql_collate': 'utf8mb4_unicode_ci'
        }
    )

    # 状态映射
    STATUS_MAPPING = {
        0: 'pending',
        1: 'confirmed',
        2: 'rejected',
        3: 'cancelled'
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

    @property
    def is_active(self):
        """是否为活跃的监护关系"""
        return self.status == 1

    def to_dict(self):
        """转换为字典格式"""
        return {
            'rule_supervision_id': self.rule_supervision_id,
            'rule_id': self.rule_id,
            'solo_user_id': self.solo_user_id,
            'supervisor_user_id': self.supervisor_user_id,
            'status': self.status,
            'status_name': self.status_name,
            'invitation_message': self.invitation_message,
            'invited_by_user_id': self.invited_by_user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'responded_at': self.responded_at.isoformat() if self.responded_at else None
        }
