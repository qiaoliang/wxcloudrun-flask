"""
社区服务模块
处理社区相关的核心业务逻辑
"""

import logging
import os
from datetime import datetime
from hashlib import sha256
from database import get_database
from database.models import User, Community, CommunityApplication, UserAuditLog

logger = logging.getLogger('log')

# 获取数据库实例
db = get_database()

# 默认社区配置
DEFAULT_COMMUNITY_NAME = "安卡大家庭"
DEFAULT_ADMIN_PHONE = "+8613900007997"
DEFAULT_ADMIN_PASSWORD = "Firefox0820"


class CommunityService:
    """社区服务类"""

    @staticmethod
    def get_or_create_default_community():
        """获取或创建默认社区"""
        with db.get_session() as session:
            community = session.query(Community).filter_by(name=DEFAULT_COMMUNITY_NAME).first()

            if not community:
                logger.info(f"创建默认社区: {DEFAULT_COMMUNITY_NAME}")

            # 确保超级管理员存在
            admin_user = CommunityService._ensure_super_admin_exists()

            # 创建默认社区
            community = Community(
                name=DEFAULT_COMMUNITY_NAME,
                description="系统默认社区，新注册用户自动加入",
                creator_user_id=admin_user.user_id,
                status=1,  # 启用
                is_default=True,
                settings={
                    "max_users": 10000,
                    "auto_approve": False
                }
            )
            db.session.add(community)
            db.session.flush()  # 获取community_id

            # 将超级管理员设为社区主管
            from .model_community_extensions import CommunityStaff
            staff_role = CommunityStaff(
                community_id=community.community_id,
                user_id=admin_user.user_id,
                role='manager'  # 主管
            )
            db.session.add(staff_role)

            # 记录审计日志
            audit_log = UserAuditLog(
                user_id=admin_user.user_id,
                action="create_default_community",
                detail=f"创建默认社区: {DEFAULT_COMMUNITY_NAME}"
            )
            db.session.add(audit_log)

            db.session.commit()
            logger.info(f"默认社区创建成功，ID: {community.community_id}")

        return community

    @staticmethod
    def _ensure_super_admin_exists():
        """确保超级管理员账户存在"""
        # 标准化电话号码格式
        from .utils.validators import normalize_phone_number
        normalized_phone = normalize_phone_number(DEFAULT_ADMIN_PHONE)

        # 使用phone_hash查找超级管理员
        phone_secret = os.getenv('PHONE_ENC_SECRET', 'default_secret')
        phone_hash = sha256(f"{phone_secret}:{normalized_phone}".encode('utf-8')).hexdigest()

        admin_user = User.query.filter_by(phone_hash=phone_hash).first()

        if not admin_user:
            logger.info(f"创建超级管理员账户: {DEFAULT_ADMIN_PHONE}")

            # 创建超级管理员账户
            from secrets import token_hex
            salt = token_hex(8)
            pwd_hash = sha256(f"{DEFAULT_ADMIN_PASSWORD}:{salt}".encode('utf-8')).hexdigest()

            admin_user = User(
                wechat_openid=f"admin_{normalized_phone}",
                phone_number=normalized_phone,
                phone_hash=phone_hash,
                password_hash=pwd_hash,
                password_salt=salt,
                nickname="系统超级管理员",
                role=4,  # 社区超级管理员
                status=1,
                verification_status=2,  # 已通过验证
                # 超级管理员拥有所有权限
                is_community_worker=True
            )
            db.session.add(admin_user)
            db.session.flush()  # 获取user_id

            # 记录审计日志
            audit_log = UserAuditLog(
                user_id=admin_user.user_id,
                action="create_super_admin",
                detail=f"创建超级管理员账户: {DEFAULT_ADMIN_PHONE}"
            )
            db.session.add(audit_log)

            db.session.commit()
            logger.info(f"超级管理员账户创建成功，ID: {admin_user.user_id}")

        return admin_user

    @staticmethod
    def assign_user_to_community(user, community_name=None):
        """将用户分配到社区"""
        if community_name is None:
            community_name = DEFAULT_COMMUNITY_NAME

        community = Community.query.filter_by(name=community_name).first()
        if not community:
            raise ValueError(f"社区不存在: {community_name}")

        # 更新用户的社区ID
        user.community_id = community.community_id
        db.session.commit()

        logger.info(f"用户 {user.user_id} 已分配到社区 {community.community_id}")
        return community

    @staticmethod
    def create_community(name, description, creator_id, location=None, settings=None):
        """创建新社区"""
        # 检查社区名称是否已存在
        existing = Community.query.filter_by(name=name).first()
        if existing:
            raise ValueError("社区名称已存在")

        # 创建社区
        community = Community(
            name=name,
            description=description,
            creator_user_id=creator_id,
            location=location,
            settings=settings or {}
        )
        db.session.add(community)
        db.session.flush()  # 获取community_id

        # 创建者自动成为主管
        from .model_community_extensions import CommunityStaff
        staff_role = CommunityStaff(
            community_id=community.community_id,
            user_id=creator_id,
            role='manager'  # 主管
        )
        db.session.add(staff_role)

        # 记录审计日志
        audit_log = UserAuditLog(
            user_id=creator_id,
            action="create_community",
            detail=f"创建社区: {name}"
        )
        db.session.add(audit_log)

        db.session.commit()
        logger.info(f"社区创建成功: {name}, ID: {community.community_id}")
        return community

    @staticmethod
    def add_community_admin(community_id, user_id, role=2, operator_id=None):
        """添加社区管理员"""
        # 导入新的CommunityStaff模型
        from .model_community_extensions import CommunityStaff
        
        # 将role值映射到新的角色系统
        # role: 1(主管理员) -> 'manager', 2(普通管理员) -> 'staff'
        role_mapping = {1: 'manager', 2: 'staff'}
        staff_role = role_mapping.get(role, 'staff')
        
        # 检查用户是否已经是该社区的管理员
        existing = CommunityStaff.query.filter_by(
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
        # 导入新的CommunityStaff模型
        from .model_community_extensions import CommunityStaff
        
        # 从CommunityStaff表中查找
        staff_record = CommunityStaff.query.filter_by(
            community_id=community_id,
            user_id=user_id
        ).first()

        if not staff_record:
            raise ValueError("用户不是该社区的管理员")

        # 检查是否是唯一的主管理员
        if staff_record.role == 'manager':
            manager_count = CommunityStaff.query.filter_by(
                community_id=community_id,
                role='manager'
            ).count()
            if manager_count <= 1:
                raise ValueError("不能移除唯一的主管理员")

        # 删除CommunityStaff记录
        db.session.delete(staff_record)

        # 记录审计日志
        audit_log = UserAuditLog(
            user_id=operator_id,
            action="remove_community_admin",
            detail=f"移除社区管理员: 社区ID={community_id}, 用户ID={user_id}"
        )
        db.session.add(audit_log)

        db.session.commit()
        logger.info(f"社区管理员移除成功: 社区ID={community_id}, 用户ID={user_id}")

    @staticmethod
    def process_application(application_id, approve, processor_id, rejection_reason=None):
        """处理社区申请"""
        application = CommunityApplication.query.get(application_id)
        if not application:
            raise ValueError("申请不存在")

        if application.status != 1:  # 不是待审核状态
            raise ValueError("申请已被处理")

        if approve:
            # 批准申请
            application.status = 2  # 已批准
            application.processed_by = processor_id
            application.updated_at = datetime.now()

            # 将用户加入社区
            user = User.query.get(application.user_id)
            user.community_id = application.target_community_id

            # 记录审计日志
            audit_log = UserAuditLog(
                user_id=processor_id,
                action="approve_community_application",
                detail=f"批准社区申请: 申请ID={application_id}, 用户ID={application.user_id}"
            )
            db.session.add(audit_log)

            logger.info(f"社区申请批准: 申请ID={application_id}")
        else:
            # 拒绝申请
            if not rejection_reason:
                raise ValueError("拒绝申请必须提供理由")

            application.status = 3  # 已拒绝
            application.rejection_reason = rejection_reason
            application.processed_by = processor_id
            application.updated_at = datetime.now()

            # 记录审计日志
            audit_log = UserAuditLog(
                user_id=processor_id,
                action="reject_community_application",
                detail=f"拒绝社区申请: 申请ID={application_id}, 理由={rejection_reason}"
            )
            db.session.add(audit_log)

            logger.info(f"社区申请拒绝: 申请ID={application_id}, 理由={rejection_reason}")

        db.session.commit()
        return application

    @staticmethod
    def search_community_users(community_id, keyword=None, page=1, per_page=20):
        """搜索社区用户（非管理员）"""
        query = User.query.filter_by(community_id=community_id)

        # 排除社区管理员
        from .model_community_extensions import CommunityStaff
        admin_user_ids = db.session.query(CommunityStaff.user_id).filter_by(
            community_id=community_id
        ).subquery()
        query = query.filter(~User.user_id.in_(admin_user_ids))

        if keyword:
            # 判断是电话号码还是昵称
            if keyword.isdigit() and len(keyword) >= 7:
                # 电话号码精确搜索
                phone_secret = os.getenv('PHONE_ENC_SECRET', 'default_secret')
                phone_hash = sha256(f"{phone_secret}:{keyword}".encode('utf-8')).hexdigest()
                query = query.filter_by(phone_hash=phone_hash)
            else:
                # 昵称模糊搜索
                query = query.filter(User.nickname.like(f"%{keyword}%"))

        # 分页
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        return pagination

    @staticmethod
    def get_available_communities():
        """获取可申请的社区列表（排除默认社区）"""
        return Community.query.filter(
            Community.status == 1,  # 启用状态
            Community.is_default == False  # 非默认社区
        ).all()