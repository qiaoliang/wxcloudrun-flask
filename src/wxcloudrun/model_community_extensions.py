"""
社区管理扩展模型
包含工作人员和成员的多对多关联表
"""

from datetime import datetime
from wxcloudrun import db


# 社区工作人员关联表 (多对多关系)
class CommunityStaff(db.Model):
    """
    社区工作人员关联表
    支持一个用户在多个社区担任工作人员
    角色: manager(主管) 或 staff(专员)
    """
    __tablename__ = 'community_staff'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    community_id = db.Column(db.Integer, db.ForeignKey('communities.community_id'), nullable=False, comment='社区ID')
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, comment='用户ID')
    role = db.Column(db.String(20), nullable=False, comment='角色: manager(主管) 或 staff(专员)')
    scope = db.Column(db.String(200), comment='负责范围(仅专员有此字段)')
    added_at = db.Column(db.DateTime, default=datetime.now, comment='添加时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关联关系
    community = db.relationship('Community', backref='staff_members')
    user = db.relationship('User', backref='staff_roles')
    
    # 索引和约束
    __table_args__ = (
        db.Index('idx_community_staff_community', 'community_id'),
        db.Index('idx_community_staff_user', 'user_id'),
        db.Index('idx_community_staff_role', 'role'),
        # 移除唯一约束，允许用户在多个社区任职
        # db.UniqueConstraint('community_id', 'user_id', name='uq_community_staff'),
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'community_id': self.community_id,
            'user_id': self.user_id,
            'role': self.role,
            'scope': self.scope,
            'added_at': self.added_at.isoformat() if self.added_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# 社区成员关联表 (多对多关系)
class CommunityMember(db.Model):
    """
    社区成员关联表
    支持一个用户属于多个社区
    """
    __tablename__ = 'community_members'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    community_id = db.Column(db.Integer, db.ForeignKey('communities.community_id'), nullable=False, comment='社区ID')
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, comment='用户ID')
    joined_at = db.Column(db.DateTime, default=datetime.now, comment='加入时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关联关系
    community = db.relationship('Community', backref='members')
    user = db.relationship('User', backref='community_memberships')
    
    # 索引和约束
    __table_args__ = (
        db.Index('idx_community_members_community', 'community_id'),
        db.Index('idx_community_members_user', 'user_id'),
        db.UniqueConstraint('community_id', 'user_id', name='uq_community_member'),
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'community_id': self.community_id,
            'user_id': self.user_id,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
