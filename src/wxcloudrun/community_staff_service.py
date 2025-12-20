import logging
import os
import json
from datetime import datetime
from hashlib import sha256
from .dao import get_db
from wxcloudrun.user_service import UserService
from database.models import User, Community, CommunityStaff,CommunityApplication, UserAuditLog
from const_default import DEFUALT_COMMUNITY_NAME,DEFUALT_COMMUNITY_ID
logger = logging.getLogger('CommunityService')

class CommunityStaffService:
    @staticmethod
    def is_admin_of_commu(commu_id,user_id):
        user_data = UserService.query_user_by_id(user_id)
        if user_data.role == 4:  # 超级管理员
            return user_data
        db = get_db()
        with db.get_session() as session:
            if not commu_id:
                raise ValueError(f'Invalid community ID, {commu_id}')

            any_manager = session.query(CommunityStaff).filter_by(
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
        db = get_db()
        with db.get_session() as session:
            staff_record = session.query(CommunityStaff).filter_by(
                user_id=user_id
            ).first()
            return staff_record is not None