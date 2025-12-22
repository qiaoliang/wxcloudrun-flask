"""
社区服务模块 - Flask-SQLAlchemy版本
处理社区相关的核心业务逻辑
"""

import logging
import os
import json
from datetime import datetime
from hashlib import sha256
from database.flask_models import db, User, Community, CommunityApplication, UserAuditLog
from const_default import DEFUALT_COMMUNITY_NAME,DEFUALT_COMMUNITY_ID,DEFAULT_BLACK_ROOM_NAME,DEFAULT_BLACK_ROOM_ID
logger = logging.getLogger('CommunityService')


class CommunityService:
    """社区服务类"""

    @staticmethod
    def assign_user_to_community(user, community_name):
        """将用户分配到社区"""
        if not community_name:
            raise ValueError("社区名称不能为空")

        community = db.session.query(Community).filter_by(name=community_name).first()
        if not community:
            raise ValueError(f"社区不存在: {community_name}")

        # 更新用户的社区ID
        user.community_id = community.community_id
        db.session.merge(user)
        db.session.commit()

        logger.info(f"用户 {user.user_id} 已分配到社区 {community.community_id}")
        return community

    @staticmethod
    def query_community_by_id(comm_id):
        """根据ID查询社区"""
        existing = db.session.query(Community).filter_by(community_id=comm_id).first()
        return existing

    @staticmethod
    def query_community_by_name(comm_name):
        """根据名称查询社区"""
        existing = db.session.query(Community).filter_by(name=comm_name).first()
        return existing

    @staticmethod
    def create_community(name, description, creator_id, location=None, settings=None, manager_id=None, location_lat=None, location_lon=None):
        """创建新社区"""
        # 检查社区名称是否已存在
        existing = db.session.query(Community).filter_by(name=name).first()
        if existing:
            raise ValueError(f"社区名称已存在: {name}")
        
        # 创建社区
        community = Community(
            name=name,
            description=description,
            creator_id=creator_id,
            location=location,
            settings=settings or {},
            manager_id=manager_id,
            location_lat=location_lat,
            location_lon=location_lon,
            status=1,
            created_at=datetime.now()
        )
        
        db.session.add(community)
        db.session.commit()
        db.session.refresh(community)
        
        logger.info(f"创建社区成功: {community.community_id}")
        return community

    @staticmethod
    def add_community_admin(community_id, user_id, role=2, operator_id=None):
        """添加社区管理员"""
        # 导入CommunityStaff模型
        from database.flask_models import CommunityStaff

        # 将role值映射到新的角色系统
        # role: 1(主管理员) -> 'manager', 2(普通管理员) -> 'staff'
        role_mapping = {1: 'manager', 2: 'staff'}
        staff_role = role_mapping.get(role, 'staff')

        # 检查用户是否已经是该社区的管理员
        existing = db.session.query(CommunityStaff).filter_by(
            community_id=community_id,
            user_id=user_id
        ).first()

        if existing:
            raise ValueError("用户已经是该社区的管理员")

        # 添加管理员到CommunityStaff表
        staff_record = CommunityStaff(
            community_id=community_id,
            user_id=user_id,
            role=staff_role
        )
        db.session.add(staff_record)

        # 记录审计日志
        audit_log = UserAuditLog(
            user_id=operator_id or user_id,
            action="add_community_admin",
            detail=f"添加社区管理员: 社区ID={community_id}, 用户ID={user_id}, 角色={staff_role}"
        )
        db.session.add(audit_log)

        db.session.commit()
        logger.info(f"社区管理员添加成功: 社区ID={community_id}, 用户ID={user_id}, 角色={staff_role}")
        return staff_record

    @staticmethod
    def remove_community_admin(community_id, user_id, operator_id=None):
        """移除社区管理员"""
        from database.flask_models import CommunityStaff

        # 查找管理员记录
        staff_record = db.session.query(CommunityStaff).filter_by(
            community_id=community_id,
            user_id=user_id
        ).first()

        if not staff_record:
            raise ValueError("用户不是该社区的管理员")

        # 删除管理员记录
        db.session.delete(staff_record)

        # 记录审计日志
        audit_log = UserAuditLog(
            user_id=operator_id or user_id,
            action="remove_community_admin",
            detail=f"移除社区管理员: 社区ID={community_id}, 用户ID={user_id}"
        )
        db.session.add(audit_log)

        db.session.commit()
        logger.info(f"社区管理员移除成功: 社区ID={community_id}, 用户ID={user_id}")
        return True

    @staticmethod
    def get_communities_with_filters(filters=None, page=1, limit=20):
        """根据筛选条件获取社区列表"""
        query = db.session.query(Community)
        
        if filters:
            if 'name' in filters:
                query = query.filter(Community.name.like(f"%{filters['name']}%"))
            if 'status' in filters:
                query = query.filter(Community.status == filters['status'])
        
        # 分页
        offset = (page - 1) * limit
        communities = query.offset(offset).limit(limit).all()
        total = query.count()
        
        return communities, total

    # 继续添加其他方法...