"""
用户服务模块 - Flask-SQLAlchemy版本
处理用户相关的核心业务逻辑
"""

import logging
import os
import json
import secrets
import time
import threading
from datetime import datetime
from hashlib import sha256
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import joinedload

# 导入Flask-SQLAlchemy模型和实例
from database.flask_models import db, User, UserAuditLog, Community

# 导入工具函数
from wxcloudrun.utils.validators import generate_phone_hash
from app.shared.utils.transaction import transactional
from app.shared.constants.roles import Role

# 全局计数器，用于生成唯一的测试手机号
_phone_counter = 0
_phone_counter_lock = threading.Lock()

# 超级系统管理员手机号，需要避免生成这个号码
SUPER_ADMIN_PHONE = '13141516171'

# 哈希相关常量
PWD_SALT = secrets.token_hex(8)
PHONE_SALT = os.getenv('PHONE_ENC_SECRET', 'default_secret')

# 哈希函数
def pwd_hash(pwd):
    return sha256(f"{pwd}:{PWD_SALT}".encode('utf-8')).hexdigest()

def phone_hash(phone_number):
    return generate_phone_hash(phone_number)

def sms_code_hash(phone, code, salt):
    """生成验证码哈希值"""
    return sha256(f"{phone}:{code}:{salt}".encode('utf-8')).hexdigest()

def random_str(length):
    """生成随机字符串"""
    length = length if length < 16 else 16
    timestamp = str(int(time.time() * 1000000))
    result = f"{timestamp}"
    return result[:length]

logger = logging.getLogger('UserService')

class UserService:
    """用户业务服务 - Flask-SQLAlchemy版本"""

    @staticmethod
    def query_user_by_refresh_token(refresh_token):
        """
        根据refresh token查询用户
        """
        try:
            stmt = select(User).where(User.refresh_token == refresh_token)
            user = db.session.execute(stmt).scalar_one_or_none()
            return user
        except Exception as e:
            logger.error(f'查询用户失败: {str(e)}')
            return None

    @staticmethod
    @transactional
    def update_user_by_id(user):
        """
        根据ID更新用户信息
        :param user: User实体
        """
        logger.info(f"update_user_by_id: 开始更新用户 user_id={user.user_id}, community_id={user.community_id}")

        # 在数据库中查找现有用户
        stmt = select(User).where(User.user_id == user.user_id)
        existing_user = db.session.execute(stmt).scalar_one_or_none()
        if not existing_user:
            logger.warning(f"update_user_by_id: 未找到用户 user_id={user.user_id}")
            return

        logger.info(f"update_user_by_id: existing_user community_id={existing_user.community_id}")

        # 更新字段
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
            if isinstance(user.role, int):
                existing_user.role = user.role
        if user.verification_status is not None:
            existing_user.verification_status = user.verification_status
        if user.verification_materials is not None:
            existing_user.verification_materials = user.verification_materials
        if user.community_id is not None:
            existing_user.community_id = user.community_id
            logger.info(f"update_user_by_id: 更新 community_id={user.community_id}")
        if user.status is not None:
            if isinstance(user.status, int):
                existing_user.status = user.status
        if user.refresh_token is not None:
            existing_user.refresh_token = user.refresh_token
        if user.refresh_token_expire is not None:
            existing_user.refresh_token_expire = user.refresh_token_expire
        if user.password_hash is not None:
            existing_user.password_hash = user.password_hash
        if user.password_salt is not None:
            existing_user.password_salt = user.password_salt
        existing_user.updated_at = user.updated_at or datetime.now()

        # 刷新到数据库，但不提交（由调用方决定是否提交）
        db.session.flush()

        logger.info(f"update_user_by_id: 完成更新 user community_id={user.community_id}")

    @staticmethod
    def query_user_by_openid(openid):
        """
        根据微信OpenID查询用户实体
        :param openid: 微信OpenID
        :return: User实体
        """
        try:
            stmt = select(User).options(joinedload(User.community)).where(
                User.wechat_openid == openid
            )
            user = db.session.execute(stmt).scalar_one_or_none()
            return user
        except OperationalError as e:
            logger.info(f"query_user_by_openid errorMsg= {e}")
            return None

    @staticmethod
    def query_user_by_phone_hash(phone_hash):
        """
        根据手机号哈希查询用户实体（包含社区关联）
        :param phone_hash: 手机号哈希值
        :return: User实体
        """
        try:
            stmt = select(User).options(joinedload(User.community)).where(
                User.phone_hash == phone_hash
            )
            user = db.session.execute(stmt).scalar_one_or_none()
            if user:
                logger.info(f"query_user_by_phone_hash: user_id={user.user_id}, community_id={user.community_id}, phone_number={user.phone_number}")
            return user
        except OperationalError as e:
            logger.info(f"query_user_by_phone_hash errorMsg= {e}")
            return None

    @staticmethod
    def query_user_by_id(user_id):
        """根据ID获取用户
        :param user_id: 用户ID
        :return: User实体
        """
        stmt = select(User).where(User.user_id == user_id)
        user = db.session.execute(stmt).scalar_one_or_none()
        return user

    @staticmethod
    def query_user_by_phone_number(phone_number):
        """根据手机号查询用户
        :param phone_number: 手机号
        :return: User实体
        """
        stmt = select(User).where(User.phone_hash == generate_phone_hash(phone_number))
        user = db.session.execute(stmt).scalar_one_or_none()
        return user

    @staticmethod
    def is_user_existed(user):
        # 如果传入的是整数，直接按 user_id 查询
        if isinstance(user, int):
            return UserService.query_user_by_id(user)

        # 只有当 user_id 不为 None 时才查询（已存在的用户）
        if hasattr(user, 'user_id') and user.user_id is not None:
            existing = UserService.query_user_by_id(user.user_id)
            if existing:
                return existing

        # 只有当 wechat_openid 不为 None 且不为空时才查询
        if hasattr(user, 'wechat_openid') and user.wechat_openid:
            existing = UserService.query_user_by_openid(user.wechat_openid)
            if existing:
                return existing

        # 只有当 phone_number 不为 None 且不为空时才查询
        if hasattr(user, 'phone_number') and user.phone_number:
            existing = UserService.query_user_by_phone_number(user.phone_number)
            if existing:
                return existing

        return None

    @staticmethod
    def _is_wechat_user(new_user):
        return (new_user.wechat_openid is not None and new_user.wechat_openid != "")

    @staticmethod
    @transactional
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
            from wxcloudrun.utils.validators import normalize_phone_number
            normalized_phone = normalize_phone_number(new_user.phone_number)
            if not normalized_phone or len(normalized_phone) < 11:
                raise ValueError("手机号格式无效")

        existing = UserService.is_user_existed(new_user)
        if existing:
            raise ValueError("用户已存在")

        if UserService._is_wechat_user(new_user):  # 微信注册用户
            new_user.phone_number = None
            new_user.phone_hash = None
            new_user.password_hash = ""
            new_user.password_salt = PWD_SALT
        else:  # phone 注册用户
            # 保存原始号码用于生成哈希
            original_phone = new_user.phone_number

            # 生成脱敏号码用于显示
            from wxcloudrun.utils.validators import _mask_phone_number
            masked_phone = _mask_phone_number(original_phone)

            new_user.phone_number = masked_phone  # 存储脱敏号码
            new_user.phone_hash = generate_phone_hash(original_phone)  # 哈希值使用原始号码
            new_user.password_hash = pwd_hash(new_user.password)
            new_user.password_salt = PWD_SALT
            new_user.wechat_openid = None
            # Only set defaults if not provided
            if not new_user.nickname:
                new_user.nickname = "用户_" + random_str(5)
            if not new_user.avatar_url:
                new_user.avatar_url = "http://exampl.com/1.jpg"

        # 以下为新用户的默认值
        new_user.name = new_user.nickname  # 用户名都使用 nickname
        new_user.role = 1  # 默认是普通用户
        new_user.community_id = 1  # 默认为'安卡大家庭'
        new_user.community_joined_at = datetime.now()  # 设置加入社区时间
        new_user.status = 1
        new_user.verification_status = 2
        new_user._is_community_worker = False

        # 添加到数据库
        db.session.add(new_user)
        db.session.flush()  # 刷新以获取数据库生成的ID

        # 记录审计日志
        audit_log = UserAuditLog(
            user_id=new_user.user_id,
            action="create_user",
            detail=f"创建用户: {new_user.user_id}"
        )
        db.session.add(audit_log)

        logger.info(f"用户创建成功: {new_user.nickname}, ID: {new_user.user_id}")
        return new_user

    @staticmethod
    def search_ankafamily_users(keyword, page=1, per_page=20):
        """
        从安卡大家庭搜索用户

        Args:
            keyword (str): 搜索关键词（昵称或手机号）
            page (int): 页码，默认1
            per_page (int): 每页数量，默认20，最大100

        Returns:
            dict: 包含用户列表和分页信息的字典
        """
        try:
            # 参数验证
            if page < 1:
                page = 1
            if per_page < 1:
                per_page = 20
            elif per_page > 100:
                per_page = 100

            # 如果关键词为空，返回空结果
            if not keyword or len(keyword) < 1:
                logger.info(f'搜索关键词为空，返回空结果')
                return {
                    'users': [],
                    'pagination': {
                        'page': page,
                        'per_page': per_page,
                        'total': 0,
                        'has_more': False
                    }
                }

            # 构建查询 - 只从安卡大家庭搜索
            from const_default import DEFAULT_COMMUNITY_ID
            from sqlalchemy import or_, func

            logger.info(f'开始搜索安卡大家庭用户: keyword="{keyword}", page={page}, per_page={per_page}, DEFAULT_COMMUNITY_ID={DEFAULT_COMMUNITY_ID}')

            # 处理搜索关键词：如果是完整手机号（11位数字），需要脱敏后搜索
            # 因为数据库中存储的是脱敏后的手机号（如 138****1234）
            search_keyword = keyword
            if keyword and len(keyword) == 11 and keyword.isdigit():
                from wxcloudrun.utils.validators import _mask_phone_number
                search_keyword = _mask_phone_number(keyword)
                logger.info(f'检测到完整手机号搜索，转换为脱敏号码搜索: "{keyword}" -> "{search_keyword}"')

            stmt_count = select(func.count()).select_from(User).where(User.community_id == DEFAULT_COMMUNITY_ID)

            # 关键词搜索（昵称或手机号）
            stmt_count = stmt_count.where(
                or_(
                    User.nickname.ilike(f'%{search_keyword}%'),
                    User.phone_number.ilike(f'%{search_keyword}%')
                )
            )

            # 计算总数
            total_count = db.session.execute(stmt_count).scalar()
            logger.info(f'符合条件的用户总数: {total_count}')

            # 分页查询 - 使用 left join 获取社区名称（即使社区不存在也能返回用户）
            offset = (page - 1) * per_page
            stmt = select(User, Community).outerjoin(Community, User.community_id == Community.community_id)
            stmt = stmt.where(User.community_id == DEFAULT_COMMUNITY_ID)
            stmt = stmt.where(
                or_(
                    User.nickname.ilike(f'%{search_keyword}%'),
                    User.phone_number.ilike(f'%{search_keyword}%')
                )
            )
            stmt = stmt.order_by(User.created_at.desc()).offset(offset).limit(per_page)
            results = db.session.execute(stmt).all()
            logger.info(f'数据库查询返回 {len(results)} 条记录')

            # 格式化响应数据
            # 使用子查询一次性获取所有工作人员的用户ID，避免 N+1 查询问题
            from database.flask_models import CommunityStaff
            staff_user_ids = db.session.execute(
                select(CommunityStaff.user_id).distinct()
            ).scalars().all()
            staff_user_ids_set = set(staff_user_ids)

            result = []
            for row in results:
                # 处理查询结果：row 可能是 (User, Community) 元组，或者是 User 对象
                if isinstance(row, tuple):
                    u, community = row
                else:
                    u = row
                    community = None

                # 使用集合查找，避免循环查询
                is_staff = u.user_id in staff_user_ids_set

                user_data = {
                    'user_id': str(u.user_id),
                    'nickname': u.nickname or '未设置昵称',
                    'avatar_url': u.avatar_url,
                    'phone_number': u.phone_number or '未设置手机号',
                    'community_id': str(u.community_id) if u.community_id else None,
                    'community_name': community.name if community else '未知社区',
                    'created_at': u.created_at.isoformat() if u.created_at else None,
                    'is_staff': is_staff
                }

                result.append(user_data)

            logger.info(f'从安卡大家庭搜索用户成功: 关键词-{keyword}, 第{page}页, 每页{per_page}条, 共{total_count}人, 本次返回{len(result)}人')

            return {
                'users': result,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_count,
                    'has_more': (page * per_page) < total_count
                }
            }

        except Exception as e:
            logger.error(f'从安卡大家庭搜索用户失败: {str(e)}', exc_info=True)
            raise

    @staticmethod
    def search_users(keyword, page=1, per_page=20, community_id=None):
        """
        搜索用户（全局搜索，支持社区过滤）

        Args:
            keyword (str): 搜索关键词
            page (int): 页码，默认1
            per_page (int): 每页数量，默认20，最大100
            community_id (int): 社区ID过滤，用于排除当前社区工作人员

        Returns:
            dict: 包含用户列表和分页信息的字典
        """
        try:
            # 参数验证
            if page < 1:
                page = 1
            if per_page < 1:
                per_page = 20
            elif per_page > 100:
                per_page = 100

            # 如果关键词为空，返回空结果
            if not keyword or len(keyword) < 1:
                return {
                    'users': [],
                    'pagination': {
                        'page': page,
                        'per_page': per_page,
                        'total': 0,
                        'has_more': False
                    }
                }

            # 构建基础查询
            from database.flask_models import CommunityStaff
            from sqlalchemy import or_, func

            stmt_count = select(func.count()).select_from(User).where(
                or_(
                    User.nickname.ilike(f'%{keyword}%'),
                    User.phone_number.ilike(f'%{keyword}%')
                )
            )

            # 角色过滤：排除超级管理员 (role=4)
            stmt_count = stmt_count.where(User.role != Role.SUPER_ADMIN)

            total_count = db.session.execute(stmt_count).scalar()

            # 分页查询
            offset = (page - 1) * per_page
            stmt = select(User).where(
                or_(
                    User.nickname.ilike(f'%{keyword}%'),
                    User.phone_number.ilike(f'%{keyword}%')
                )
            )
            stmt = stmt.where(User.role != Role.SUPER_ADMIN)
            stmt = stmt.order_by(User.created_at.desc()).offset(offset).limit(per_page)
            users = db.session.execute(stmt).scalars().all()

            # 格式化响应数据
            # 使用子查询一次性获取所有工作人员信息，避免 N+1 查询问题
            from database.flask_models import CommunityStaff
            all_staff = db.session.execute(
                select(CommunityStaff.user_id, CommunityStaff.community_id, CommunityStaff.role)
            ).all()

            # 构建字典以便快速查找
            staff_dict = {}
            for staff_user_id, staff_community_id, staff_role in all_staff:
                if staff_user_id not in staff_dict:
                    staff_dict[staff_user_id] = []
                staff_dict[staff_user_id].append({'community_id': staff_community_id, 'role': staff_role})

            result = []
            for u in users:
                # 检查是否是当前社区的工作人员
                is_current_community_staff = False
                current_community_manager = False
                other_community_manager = False

                if community_id:
                    user_staff = staff_dict.get(u.user_id, [])
                    for staff_info in user_staff:
                        if staff_info['community_id'] == community_id:
                            if staff_info['role'] == 'staff':
                                is_current_community_staff = True
                            elif staff_info['role'] == 'manager':
                                current_community_manager = True
                        elif staff_info['role'] == 'manager':
                            other_community_manager = True

                user_data = {
                    'user_id': str(u.user_id),
                    'wechat_openid': u.wechat_openid,
                    'phone_number': u.phone_number,
                    'nickname': u.nickname or '未设置昵称',
                    'name': u.name,
                    'avatar_url': u.avatar_url,
                    'role': u.role,
                    'community_id': str(u.community_id) if u.community_id else None,
                    'status': u.status,
                    'created_at': u.created_at.isoformat() if u.created_at else None,
                    'is_current_community_staff': is_current_community_staff,
                    'is_current_community_manager': current_community_manager,
                    'is_other_community_manager': other_community_manager,
                    'is_staff': db.session.execute(select(CommunityStaff).where(
                        CommunityStaff.user_id == u.user_id,
                        CommunityStaff.removed_at.is_(None)
                    )).scalar_one_or_none() is not None
                }

                result.append(user_data)

            has_more = (page * per_page) < total_count

            logger.info(f'搜索用户成功: 关键词-{keyword}, 第{page}页, 每页{per_page}条, 共{total_count}人, 本次返回{len(result)}人')

            return {
                'users': result,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_count,
                    'has_more': has_more
                }
            }

        except Exception as e:
            logger.error(f'搜索用户失败: {str(e)}', exc_info=True)
            raise

    @staticmethod
    def search_users_by_phone(normalized_phone, page=1, per_page=20):
        """
        按手机号搜索用户

        Args:
            normalized_phone (str): 标准化的手机号
            page (int): 页码，默认1
            per_page (int): 每页数量，默认20，最大100

        Returns:
            dict: 包含用户列表和分页信息的字典
        """
        try:
            # 参数验证
            if page < 1:
                page = 1
            if per_page < 1:
                per_page = 20
            elif per_page > 100:
                per_page = 100

            # 搜索用户
            from sqlalchemy import func
            stmt_count = select(func.count()).select_from(User).where(
                User.phone_number.ilike(f'%{normalized_phone}%')
            )
            stmt_count = stmt_count.where(User.role != Role.SUPER_ADMIN)  # 排除超级管理员

            total_count = db.session.execute(stmt_count).scalar()

            # 分页查询
            offset = (page - 1) * per_page
            stmt = select(User).where(
                User.phone_number.ilike(f'%{normalized_phone}%')
            )
            stmt = stmt.where(User.role != Role.SUPER_ADMIN)  # 排除超级管理员
            stmt = stmt.order_by(User.created_at.desc()).offset(offset).limit(per_page)
            users = db.session.execute(stmt).scalars().all()

            # 格式化响应数据
            result = []
            for u in users:
                user_data = {
                    'user_id': str(u.user_id),
                    'wechat_openid': u.wechat_openid,
                    'phone_number': u.phone_number,
                    'nickname': u.nickname or '未设置昵称',
                    'name': u.name,
                    'avatar_url': u.avatar_url,
                    'role': u.role,
                    'community_id': str(u.community_id) if u.community_id else None,
                    'status': u.status,
                    'created_at': u.created_at.isoformat() if u.created_at else None,
                    'is_staff': db.session.execute(select(CommunityStaff).where(
                        CommunityStaff.user_id == u.user_id,
                        CommunityStaff.removed_at.is_(None)
                    )).scalar_one_or_none() is not None
                }

                result.append(user_data)

            has_more = (page * per_page) < total_count

            return {
                'users': result,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_count,
                    'has_more': has_more
                }
            }

        except Exception as e:
            logger.error(f'按手机号搜索用户失败: {str(e)}', exc_info=True)
            raise

    @staticmethod
    def search_users_by_nickname(keyword, page=1, per_page=20):
        """
        按昵称搜索用户

        Args:
            keyword (str): 搜索关键词
            page (int): 页码，默认1
            per_page (int): 每页数量，默认20，最大100

        Returns:
            dict: 包含用户列表和分页信息的字典
        """
        try:
            # 参数验证
            if page < 1:
                page = 1
            if per_page < 1:
                per_page = 20
            elif per_page > 100:
                per_page = 100

            # 搜索用户
            stmt_count = select(func.count()).select_from(User).where(
                User.nickname.ilike(f'%{keyword}%')
            )
            stmt_count = stmt_count.where(User.role != Role.SUPER_ADMIN)  # 排除超级管理员

            total_count = db.session.execute(stmt_count).scalar()

            # 分页查询
            offset = (page - 1) * per_page
            stmt = select(User).where(
                User.nickname.ilike(f'%{keyword}%')
            )
            stmt = stmt.where(User.role != Role.SUPER_ADMIN)  # 排除超级管理员
            stmt = stmt.order_by(User.created_at.desc()).offset(offset).limit(per_page)
            users = db.session.execute(stmt).scalars().all()

            # 格式化响应数据
            result = []
            for u in users:
                user_data = {
                    'user_id': str(u.user_id),
                    'wechat_openid': u.wechat_openid,
                    'phone_number': u.phone_number,
                    'nickname': u.nickname or '未设置昵称',
                    'name': u.name,
                    'avatar_url': u.avatar_url,
                    'role': u.role,
                    'community_id': str(u.community_id) if u.community_id else None,
                    'status': u.status,
                    'created_at': u.created_at.isoformat() if u.created_at else None,
                    'is_staff': db.session.execute(select(CommunityStaff).where(CommunityStaff.user_id == u.user_id)).scalar_one_or_none() is not None
                }

                result.append(user_data)

            has_more = (page * per_page) < total_count

            return {
                'users': result,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_count,
                    'has_more': has_more
                }
            }

        except Exception as e:
            logger.error(f'按昵称搜索用户失败: {str(e)}', exc_info=True)
            raise

    @staticmethod
    def log_profile_view(viewer_id, viewed_user_id, community_id):
        """记录查看成员信息

        Args:
            viewer_id: 查看者ID
            viewed_user_id: 被查看用户ID
            community_id: 社区ID
        """
        from database.flask_models import ProfileViewLog

        # 本人查看自己不记录
        if viewer_id == viewed_user_id:
            return

        log = ProfileViewLog(
            viewer_id=viewer_id,
            viewed_user_id=viewed_user_id,
            community_id=community_id,
            view_type='profile'
        )
        db.session.add(log)
        db.session.flush()

    @staticmethod
    def log_view_guardian_info(viewer_id, guardian_id, ward_user_id, community_id):
        """记录查看监护人信息

        Args:
            viewer_id: 查看者ID
            guardian_id: 监护人ID
            ward_user_id: 被监护人ID
            community_id: 社区ID
        """
        from database.flask_models import ProfileViewLog

        log = ProfileViewLog(
            viewer_id=viewer_id,
            viewed_user_id=guardian_id,
            ward_user_id=ward_user_id,
            community_id=community_id,
            view_type='guardian_info'
        )
        db.session.add(log)
        db.session.flush()

    @staticmethod
    def get_profile_view_logs(community_id, viewer_id=None, limit=100):
        """获取浏览记录列表

        Args:
            community_id: 社区ID
            viewer_id: 查看者ID（可选，用于筛选）
            limit: 返回数量限制

        Returns:
            list: 浏览记录列表
        """
        from database.flask_models import ProfileViewLog
        from sqlalchemy import select, desc

        stmt = select(ProfileViewLog).where(
            ProfileViewLog.community_id == community_id
        )

        if viewer_id:
            stmt = stmt.where(ProfileViewLog.viewer_id == viewer_id)

        stmt = stmt.order_by(desc(ProfileViewLog.created_at)).limit(limit)

        logs = db.session.execute(stmt).scalars().all()

        return [log.to_dict() for log in logs]