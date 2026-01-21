"""
超级管理员和默认社区初始化模块
用于系统启动时创建必要的初始数据
"""

import logging
import secrets
import os
from hashlib import sha256
from sqlalchemy import select
from database.flask_models import User, Community, CommunityStaff, db
from wxcloudrun.utils.validators import generate_phone_hash
from app.shared.constants.roles import Role

from const_default import DEFAULT_COMMUNITY_NAME,DEFAULT_COMMUNITY_ID,BLACKHOUSE_COMMUNITY_NAME


def create_superadmin_and_default_community():
    """
    创建超级系统管理员和默认社区
    - 创建超级系统管理员
    - 创建两个默认社区（安卡大家庭和黑屋社区）
    - 将超级系统管理员设置为这两个社区的主管
    """
    logger = logging.getLogger('log')
    logger.info("开始创建超级系统管理员和默认社区...")

    try:
        # 检查超级系统管理员是否已存在
        stmt = select(User).where(User.phone_number == '13141516171')
        superadmin = db.session.execute(stmt).scalar_one_or_none()

        # 如果超级系统管理员不存在，则创建
        if not superadmin:
            logger.info("开始创建超级系统管理员...")

            # 创建超级系统管理员
            salt = secrets.token_hex(8)
            password_hash = sha256(f"F1234567:{salt}".encode('utf-8')).hexdigest()
            phone_hash = generate_phone_hash("13141516171")

            superadmin = User(
                wechat_openid=f"superadmin_{secrets.token_hex(16)}",
                phone_number='13141516171',
                phone_hash=phone_hash,
                nickname='系统超级系统管理员',
                name='系统超级系统管理员',
                password_hash=password_hash,
                password_salt=salt,
                role=Role.SUPER_ADMIN,
                status=1,
                verification_status=2,
                _is_community_worker=True,
                community_id=None,  # 暂时设为None，后续再分配
                address='北京市朝阳区柳芳南里29号'
            )
            db.session.add(superadmin)
            db.session.flush()  # 获取用户ID
            logger.info(f"超级系统管理员创建成功，ID: {superadmin.user_id}")
        else:
            # 为已存在的超级管理员设置 address（如果为空）
            if not superadmin.address:
                superadmin.address = '北京市朝阳区柳芳南里29号'
                logger.info("已为超级系统管理员设置地址")

        # 检查并创建默认社区'安卡大家庭'
        stmt = select(Community).where(Community.name == '安卡大家庭')
        default_community = db.session.execute(stmt).scalar_one_or_none()

        if not default_community:
            logger.info("开始创建默认社区'安卡大家庭'...")
            default_community = Community(
                name='安卡大家庭',
                description='系统默认社区，新注册用户自动加入',
                creator_id=superadmin.user_id,
                manager_id=superadmin.user_id,
                status=1,
                is_default=True,
                location='北京市朝阳区柳芳南里29号'
            )
            db.session.add(default_community)
            db.session.flush()  # 获取社区ID
            logger.info(f"默认社区'安卡大家庭'创建成功，ID: {default_community.community_id}")
        else:
            logger.info("默认社区'安卡大家庭'已存在")
            # 为已存在的社区设置 location（如果为空）
            if not default_community.location:
                default_community.location = '北京市朝阳区柳芳南里29号'
                logger.info("已为默认社区'安卡大家庭'设置地址")

        # 检查并创建黑屋社区
        stmt = select(Community).where(Community.name == BLACKHOUSE_COMMUNITY_NAME)
        blackhouse_community = db.session.execute(stmt).scalar_one_or_none()

        if not blackhouse_community:
            logger.info(f"开始创建黑屋社区'{BLACKHOUSE_COMMUNITY_NAME}'...")
            blackhouse_community = Community(
                name=BLACKHOUSE_COMMUNITY_NAME,
                description='特殊管理社区，用户在此社区时功能受限',
                creator_id=superadmin.user_id,
                manager_id=superadmin.user_id,
                status=1,
                is_blackhouse=True,
                location='北京市朝阳区柳芳南里29号'
            )
            db.session.add(blackhouse_community)
            db.session.flush()  # 获取社区ID
            logger.info(f"黑屋社区'{BLACKHOUSE_COMMUNITY_NAME}'创建成功，ID: {blackhouse_community.community_id}")
        else:
            logger.info(f"黑屋社区'{BLACKHOUSE_COMMUNITY_NAME}'已存在")
            # 为已存在的社区设置 location（如果为空）
            if not blackhouse_community.location:
                blackhouse_community.location = '北京市朝阳区柳芳南里29号'
                logger.info(f"已为黑屋社区'{BLACKHOUSE_COMMUNITY_NAME}'设置地址")

        # 确保超级系统管理员的community_id设置为默认社区ID
        superadmin.community_id = default_community.community_id
        
        # 确保社区的管理员字段正确设置
        default_community.manager_id = superadmin.user_id
        blackhouse_community.manager_id = superadmin.user_id
        
        # 确保在CommunityStaff表中设置主管关系
        # 检查并创建默认社区主管关系
        stmt = select(CommunityStaff).where(
            CommunityStaff.community_id == default_community.community_id,
            CommunityStaff.user_id == superadmin.user_id,
            CommunityStaff.role == 'manager'
        )
        existing_staff = db.session.execute(stmt).scalar_one_or_none()
        
        if not existing_staff:
            staff_relation = CommunityStaff(
                community_id=default_community.community_id,
                user_id=superadmin.user_id,
                role='manager'
            )
            db.session.add(staff_relation)
            logger.info(f"为超级系统管理员设置'安卡大家庭'社区主管关系")

        # 检查并创建黑屋社区主管关系
        stmt = select(CommunityStaff).where(
            CommunityStaff.community_id == blackhouse_community.community_id,
            CommunityStaff.user_id == superadmin.user_id,
            CommunityStaff.role == 'manager'
        )
        existing_staff = db.session.execute(stmt).scalar_one_or_none()
        
        if not existing_staff:
            staff_relation = CommunityStaff(
                community_id=blackhouse_community.community_id,
                user_id=superadmin.user_id,
                role='manager'
            )
            db.session.add(staff_relation)
            logger.info(f"为超级系统管理员设置'{BLACKHOUSE_COMMUNITY_NAME}'社区主管关系")

        db.session.commit()
        logger.info("超级系统管理员和默认社区初始化完成")

    except Exception as e:
        logger.error(f"创建超级管理员和默认社区失败: {str(e)}")
        db.session.rollback()
        raise