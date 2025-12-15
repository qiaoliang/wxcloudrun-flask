import logging
import os
import json
from datetime import datetime
from hashlib import sha256
from .dao import get_db
from database.models import User, Community, CommunityApplication, UserAuditLog
from const_default import DEFUALT_COMMUNITY_NAME,DEFUALT_COMMUNITY_ID
logger = logging.getLogger('CommunityService')

class CommunityStaffService:
    @staticmethod
    def is_staff(commu_id,user_id):
        db = get_db()
        with db.get_session() as session:
            # TODO:判断该用户是否为该社区的工作人员
            raise ValueError("待实现")
        pass