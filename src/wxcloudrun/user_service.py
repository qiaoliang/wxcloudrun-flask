"""
社区服务模块
处理社区相关的核心业务逻辑
"""

import logging
import os
import json
from datetime import datetime
from hashlib import sha256
from sqlalchemy.exc import OperationalError
from .dao import get_db
from database.models import User,UserAuditLog
from hashutil import pwd_hash,phone_hash,sms_code_hash,PWD_SALT,PHONE_SALT,random_str

logger = logging.getLogger('log')

class UserService:

    @staticmethod
    def update_user_by_id(user_to_update):
        """
        根据ID更新用户信息
        :param user: User实体
        """
        if not UserService.is_user_existed(user_to_update):
            raise

    @staticmethod
    def query_user_by_openid(openid):
        """
        根据微信OpenID查询用户实体
        :param openid: 微信OpenID
        :return: User实体
        """
        try:
            with get_db().get_session() as session:
                user = session.query(User).filter(User.wechat_openid == openid).first()
                if user:
                     session.expunge(user)
                return user
        except OperationalError as e:
            logger.info("query_user_by_openid errorMsg= {} ".format(e))
            return None
    @staticmethod
    def query_user_by_id(user_id):
        """根据ID获取社区"""
        db = get_db()
        user = None
        with db.get_session() as session:
            user= session.query(User).filter_by(user_id=user_id).first()
            if user:
                session.expunge(user)
            return user

    @staticmethod
    def query_user_by_phone_number(phone_number):
        db = get_db()
        # 检查社区名称是否已存在
        with db.get_session() as session:
            user = session.query(User).filter_by(phone_hash=phone_hash(phone_number)).first()
            if user:
                session.expunge(user)
            return user

    @staticmethod
    def is_user_existed(user):
        # 只有当 user_id 不为 None 时才查询（已存在的用户）
        if hasattr(user, 'user_id') and user.user_id is not None:
            existing = UserService.query_user_by_id(user.user_id)
            if existing:
                    return existing
        existing = UserService.query_user_by_openid(user.wechat_openid)
        if existing:
                return existing
        existing = UserService.query_user_by_phone_number(user.phone_number)
        if existing:
                return existing
        return None
    @staticmethod
    def _is_wechat_user(new_user):
        return (new_user.wechat_openid!=None and new_user.wechat_openid !="")
    @staticmethod
    def create_user(new_user):
        # 验证：必须提供 wechat_openid 或 phone_number 至少一个
        has_openid = hasattr(new_user, 'wechat_openid') and new_user.wechat_openid
        has_phone = hasattr(new_user, 'phone_number') and new_user.phone_number

        if not has_openid and not has_phone:
            raise ValueError("必须提供微信OpenID或手机号至少一个")

        # 验证：不能同时提供 wechat_openid 和 phone_number
        if has_openid and has_phone:
            raise ValueError("不能同时提供微信OpenID和手机号")

        # 验证手机号格式（如果提供了手机号）
        if has_phone:
            from .utils.validators import normalize_phone_number
            normalized_phone = normalize_phone_number(new_user.phone_number)
            if not normalized_phone or len(normalized_phone) < 11:
                raise ValueError("手机号格式无效")

        existing = UserService.is_user_existed(new_user)
        if existing:
                raise ValueError("用户已存在")

        db = get_db()
        if UserService._is_wechat_user(new_user): # 微信注册用户
            new_user.phone_number = ""
            new_user.phone_hash= ""
            new_user.password_hash = ""
            new_user.password_salt=PWD_SALT
        else: # phone 注册用户
            # 保存原始号码用于生成哈希
            original_phone = new_user.phone_number

            # 生成脱敏号码用于显示
            from .utils.validators import _mask_phone_number
            masked_phone = _mask_phone_number(original_phone)

            new_user.phone_number = masked_phone  # 存储脱敏号码
            new_user.phone_hash = phone_hash(original_phone)  # 哈希值使用原始号码
            new_user.password_hash = pwd_hash(new_user.password)
            new_user.password_salt = PWD_SALT
            new_user.wechat_openid =""
            new_user.nickname="用户_"+random_str(5)
            new_user.avatar_url="http://exampl.com/1.jpg"
        # 以下为新用户的默认值
        new_user.name=new_user.nickname  # 用户名都使用 nickname
        new_user.role = 1 # 默认是普通用户
        new_user.community_id = 1 # 默认为‘安卡大家庭’
        new_user.status=1
        new_user.verification_status=2
        new_user._is_community_worker = False
        with db.get_session() as session:
            session.add(new_user)
            session.flush()  # 刷新以获取数据库生成的ID
            session.refresh(new_user)  # 确保获取数据库生成的值

            # 记录审计日志
            audit_log = UserAuditLog(
                user_id=new_user.user_id,
                action="create_user",
                detail=f"创建用户: {new_user.user_id}"
            )
            session.add(audit_log)

            session.commit()
            session.refresh(new_user)  # 确保所有属性都已加载
            logger.info(f"用户创建成功: {new_user.nickname}, ID: {new_user.user_id}")

            # 返回字典而不是对象，避免 session 关闭后的 DetachedInstanceError
            return {
                    'user_id':new_user.user_id,
                    'wechat_openid':new_user.wechat_openid,
                    'phone_number':new_user.phone_number,
                    'phone_hash':new_user.phone_hash,
                    'nickname':new_user.nickname,
                    'name':new_user.nickname,
                    'password_hash':new_user.password_hash,
                    'role':new_user.role,  # 社区工作人员角色
                    'status':new_user.status,
                    'verification_status':new_user.verification_status,  # 已通过验证
                    '_is_community_worker':new_user._is_community_worker
                }
