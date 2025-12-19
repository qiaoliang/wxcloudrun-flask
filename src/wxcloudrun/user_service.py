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

logger = logging.getLogger('UserService')

class UserService:

    @staticmethod
    def query_user_by_refresh_token(refresh_token, session=None):
        """
        根据refresh token查询用户
        """
        try:
            # 如果session为None，创建新的会话
            if session is None:
                with get_db().get_session() as session:
                    user = session.query(User).filter(
                        User.refresh_token == refresh_token).first()
                    if user:
                        session.expunge(user)
                    return user
            else:
                # 使用传入的session
                user = session.query(User).filter(
                    User.refresh_token == refresh_token).first()
                # 注意：使用外部传入的session时，不进行expunge操作
                return user
        except Exception as e:
            logger.error(f'查询用户失败: {str(e)}')
            return None


    @staticmethod
    def update_user_by_id(user, session=None):
        """
        根据ID更新用户信息
        :param user: User实体
        :param session: 数据库会话，如果为None则创建新会话
        """
        try:
            # 如果session为None，创建新的会话
            if session is None:
                with get_db().get_session() as session:
                    # 在同一个会话中查询用户
                    existing_user = session.query(User).filter_by(user_id=user.user_id).first()
                    if existing_user is None:
                        return

                    if user.nickname is not None:
                        existing_user.nickname = user.nickname
                    if user.avatar_url is not None:
                        existing_user.avatar_url = user.avatar_url
                    if user.name is not None:
                        existing_user.name = user.name
                    if user.work_id is not None:
                        existing_user.work_id = user.work_id
                    if user.phone_number is not None:
                        existing_user.phone_number = user.phone_number
                    if user.role is not None:
                        # 如果传入的是字符串，转换为对应的整数值
                        if isinstance(user.role, str):
                            # 由于 User 模型没有 get_role_value 方法，暂时不处理字符串
                            # role_value = User.get_role_value(user.role)
                            # if role_value is not None:
                            #     existing_user.role = role_value
                            pass  # 字符串角色暂时不处理
                        elif isinstance(user.role, int):
                            existing_user.role = user.role
                    if user.verification_status is not None:
                        existing_user.verification_status = user.verification_status
                    if user.verification_materials is not None:
                        existing_user.verification_materials = user.verification_materials
                    if user.community_id is not None:
                        existing_user.community_id = user.community_id
                    if user.status is not None:
                        # 如果传入的是字符串，转换为对应的整数值
                        if isinstance(user.status, str):
                            # 由于 User 模型没有 get_status_value 方法，暂时不处理字符串
                            # status_value = User.get_status_value(user.status)
                            # if status_value is not None:
                            #     existing_user.status = status_value
                            pass  # 字符串状态暂时不处理
                        elif isinstance(user.status, int):
                            existing_user.status = user.status
                    if user.refresh_token is not None:
                        existing_user.refresh_token = user.refresh_token
                    if user.refresh_token_expire is not None:
                        existing_user.refresh_token_expire = user.refresh_token_expire
                    existing_user.updated_at = user.updated_at or datetime.now()

                    session.flush()
                    # session.commit() is handled by the context manager
            else:
                # 使用传入的session
                # 在同一个会话中查询用户
                existing_user = session.query(User).filter_by(user_id=user.user_id).first()
                if existing_user is None:
                    return

                if user.nickname is not None:
                    existing_user.nickname = user.nickname
                if user.avatar_url is not None:
                    existing_user.avatar_url = user.avatar_url
                if user.name is not None:
                    existing_user.name = user.name
                if user.work_id is not None:
                    existing_user.work_id = user.work_id
                if user.phone_number is not None:
                    existing_user.phone_number = user.phone_number
                if user.role is not None:
                    # 如果传入的是字符串，转换为对应的整数值
                    if isinstance(user.role, str):
                        # 由于 User 模型没有 get_role_value 方法，暂时不处理字符串
                        # role_value = User.get_role_value(user.role)
                        # if role_value is not None:
                        #     existing_user.role = role_value
                        pass  # 字符串角色暂时不处理
                    elif isinstance(user.role, int):
                        existing_user.role = user.role
                if user.verification_status is not None:
                    existing_user.verification_status = user.verification_status
                if user.verification_materials is not None:
                    existing_user.verification_materials = user.verification_materials
                if user.community_id is not None:
                    existing_user.community_id = user.community_id
                if user.status is not None:
                    # 如果传入的是字符串，转换为对应的整数值
                    if isinstance(user.status, str):
                        # 由于 User 模型没有 get_status_value 方法，暂时不处理字符串
                        # status_value = User.get_status_value(user.status)
                        # if status_value is not None:
                        #     existing_user.status = status_value
                        pass  # 字符串状态暂时不处理
                    elif isinstance(user.status, int):
                        existing_user.status = user.status
                if user.refresh_token is not None:
                    existing_user.refresh_token = user.refresh_token
                if user.refresh_token_expire is not None:
                    existing_user.refresh_token_expire = user.refresh_token_expire
                existing_user.updated_at = user.updated_at or datetime.now()

                session.flush()
                # 注意：使用外部传入的session时，由调用者负责commit
        except OperationalError as e:
            logger.info("update_user_by_id errorMsg= {} ".format(e))


    @staticmethod
    def query_user_by_openid(openid, session=None):
        """
        根据微信OpenID查询用户实体
        :param openid: 微信OpenID
        :param session: 数据库会话，如果为None则创建新会话
        :return: User实体
        """
        try:
            # 如果session为None，创建新的会话
            if session is None:
                with get_db().get_session() as session:
                    user = session.query(User).filter(User.wechat_openid == openid).first()
                    if user:
                         session.expunge(user)
                    return user
            else:
                # 使用传入的session
                user = session.query(User).filter(User.wechat_openid == openid).first()
                # 注意：使用外部传入的session时，不进行expunge操作
                return user
        except OperationalError as e:
            logger.info("query_user_by_openid errorMsg= {} ".format(e))
            return None
    @staticmethod
    def query_user_by_id(user_id, session=None):
        """根据ID获取社区
        :param user_id: 用户ID
        :param session: 数据库会话，如果为None则创建新会话
        :return: User实体
        """
        # 如果session为None，创建新的会话
        if session is None:
            db = get_db()
            user = None
            with db.get_session() as session:
                user= session.query(User).filter_by(user_id=user_id).first()
                if user:
                    session.expunge(user)
                return user
        else:
            # 使用传入的session
            user = session.query(User).filter_by(user_id=user_id).first()
            # 注意：使用外部传入的session时，不进行expunge操作
            return user

    @staticmethod
    def query_user_by_phone_number(phone_number, session=None):
        """根据手机号查询用户
        :param phone_number: 手机号
        :param session: 数据库会话，如果为None则创建新会话
        :return: User实体
        """
        # 如果session为None，创建新的会话
        if session is None:
            db = get_db()
            # 检查社区名称是否已存在
            with db.get_session() as session:
                user = session.query(User).filter_by(phone_hash=phone_hash(phone_number)).first()
                if user:
                    session.expunge(user)
                return user
        else:
            # 使用传入的session
            user = session.query(User).filter_by(phone_hash=phone_hash(phone_number)).first()
            # 注意：使用外部传入的session时，不进行expunge操作
            return user

    @staticmethod
    def is_user_existed(user,session=None):
        # 如果传入的是整数，直接按 user_id 查询
        if isinstance(user, int):
            return UserService.query_user_by_id(user,session)

        # 只有当 user_id 不为 None 时才查询（已存在的用户）
        if hasattr(user, 'user_id') and user.user_id is not None:
            existing = UserService.query_user_by_id(user.user_id,session)
            if existing:
                    return existing

        # 只有当 wechat_openid 不为 None 且不为空时才查询
        if hasattr(user, 'wechat_openid') and user.wechat_openid:
            existing = UserService.query_user_by_openid(user.wechat_openid,session)
            if existing:
                    return existing

        # 只有当 phone_number 不为 None 且不为空时才查询
        if hasattr(user, 'phone_number') and user.phone_number:
            existing = UserService.query_user_by_phone_number(user.phone_number,session)
            if existing:
                    return existing

        return None
    @staticmethod
    def _is_wechat_user(new_user):
        return (new_user.wechat_openid!=None and new_user.wechat_openid !="")
    @staticmethod
    def create_user(new_user, session=None):
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
            new_user.phone_number = None
            new_user.phone_hash = None
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
            new_user.wechat_openid = None
            # Only set defaults if not provided
            if not new_user.nickname:
                new_user.nickname="用户_"+random_str(5)
            if not new_user.avatar_url:
                new_user.avatar_url="http://exampl.com/1.jpg"
        # 以下为新用户的默认值
        new_user.name=new_user.nickname  # 用户名都使用 nickname
        new_user.role = 1 # 默认是普通用户
        new_user.community_id = 1 # 默认为‘安卡大家庭’
        new_user.community_joined_at = datetime.now()  # 设置加入社区时间
        new_user.status=1
        new_user.verification_status=2
        new_user._is_community_worker = False

        # 如果session为None，创建新的会话
        if session is None:
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
                session.expunge(new_user)
                return new_user
        else:
            # 使用传入的session
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

            # 注意：使用外部传入的session时，由调用者负责commit
            session.refresh(new_user)  # 确保所有属性都已加载
            logger.info(f"用户创建成功: {new_user.nickname}, ID: {new_user.user_id}")
            # 注意：使用外部传入的session时，不进行expunge操作
            return new_user
