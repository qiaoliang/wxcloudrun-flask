"""
社区工作人员服务模块 - Flask-SQLAlchemy版本
"""
import logging
import os
import json
from datetime import datetime
from hashlib import sha256
from wxcloudrun.user_service import UserService
from database.flask_models import db, User, Community, CommunityStaff, CommunityApplication, UserAuditLog
from const_default import DEFUALT_COMMUNITY_NAME, DEFUALT_COMMUNITY_ID
logger = logging.getLogger('CommunityService')


class CommunityStaffService:
    @staticmethod
    def is_admin_of_commu(commu_id, user_id):
        """检查用户是否是社区管理员"""
        user_data = UserService.query_user_by_id(user_id)
        if user_data.role == 4:  # 超级管理员
            return user_data
        
        if not commu_id:
            raise ValueError(f'Invalid community ID, {commu_id}')

        any_manager = db.session.query(CommunityStaff).filter_by(
            community_id=commu_id,
            user_id=user_id
        ).first()

        if any_manager:
            user_data = UserService.query_user_by_id(any_manager.user_id)
            return user_data
        else:
            return None

    @staticmethod
    def check_user_is_staff(user_id):
        """
        检查用户是否是任何社区的工作人员
        
        Args:
            user_id (int): 用户ID
            
        Returns:
            bool: 如果是工作人员返回True，否则返回False
        """
        staff_record = db.session.query(CommunityStaff).filter_by(
            user_id=user_id
        ).first()
        return staff_record is not None

    @staticmethod
    def add_staff(community_id, user_id, role='staff', operator_id=None):
        """
        添加社区工作人员
        
        Args:
            community_id (int): 社区ID
            user_id (int): 用户ID
            role (str): 角色 ('manager' 或 'staff')
            operator_id (int): 操作者ID
            
        Returns:
            CommunityStaff: 工作人员记录
        """
        # 检查是否已经是工作人员
        existing = db.session.query(CommunityStaff).filter_by(
            community_id=community_id,
            user_id=user_id
        ).first()
        
        if existing:
            raise ValueError("用户已经是该社区的工作人员")
        
        # 创建工作人员记录
        staff = CommunityStaff(
            community_id=community_id,
            user_id=user_id,
            role=role
        )
        db.session.add(staff)
        
        # 记录审计日志
        audit_log = UserAuditLog(
            user_id=operator_id or user_id,
            action="add_staff",
            detail=f"添加社区工作人员: 社区ID={community_id}, 用户ID={user_id}, 角色={role}"
        )
        db.session.add(audit_log)
        
        db.session.commit()
        logger.info(f"社区工作人员添加成功: 社区ID={community_id}, 用户ID={user_id}")
        return staff

    @staticmethod
    def remove_staff(community_id, user_id, operator_id=None):
        """
        移除社区工作人员
        
        Args:
            community_id (int): 社区ID
            user_id (int): 用户ID
            operator_id (int): 操作者ID
            
        Returns:
            bool: 是否成功
        """
        staff = db.session.query(CommunityStaff).filter_by(
            community_id=community_id,
            user_id=user_id
        ).first()
        
        if not staff:
            raise ValueError("用户不是该社区的工作人员")
        
        db.session.delete(staff)
        
        # 记录审计日志
        audit_log = UserAuditLog(
            user_id=operator_id or user_id,
            action="remove_staff",
            detail=f"移除社区工作人员: 社区ID={community_id}, 用户ID={user_id}"
        )
        db.session.add(audit_log)
        
        db.session.commit()
        logger.info(f"社区工作人员移除成功: 社区ID={community_id}, 用户ID={user_id}")
        return True

    @staticmethod
    def get_community_staff(community_id, role=None):
        """
        获取社区工作人员列表
        
        Args:
            community_id (int): 社区ID
            role (str): 角色筛选 (可选)
            
        Returns:
            list: 工作人员列表
        """
        query = db.session.query(CommunityStaff).filter_by(community_id=community_id)
        
        if role:
            query = query.filter_by(role=role)
        
        return query.all()

    @staticmethod
    def handle_user_community_change(user_id, old_community_id, new_community_id):
        """
        处理用户社区变更时的工作人员关系
        
        Args:
            user_id (int): 用户ID
            old_community_id (int): 旧社区ID
            new_community_id (int): 新社区ID
        """
        # 移除旧社区的工作人员关系
        if old_community_id:
            db.session.query(CommunityStaff).filter_by(
                community_id=old_community_id,
                user_id=user_id
            ).delete()
        
        # 如果新社区存在，检查是否需要添加工作人员关系
        if new_community_id:
            user = UserService.query_user_by_id(user_id)
            if user and user.role >= 2:  # 如果是管理员或以上
                staff = CommunityStaff(
                    community_id=new_community_id,
                    user_id=user_id,
                    role='manager' if user.role >= 3 else 'staff'
                )
                db.session.add(staff)
        
        db.session.commit()