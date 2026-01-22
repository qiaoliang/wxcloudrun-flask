"""
超级管理员和默认社区初始化模块
用于系统启动时创建必要的初始数据
"""

import logging
import secrets
import os
from datetime import datetime, timezone
from hashlib import sha256
from sqlalchemy import select
from database.flask_models import User, Community, CommunityStaff, CheckinRule, db
from datetime import time
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
                avatar_url='https://example.com/avatar/superadmin.png',
                work_id='SA0000001',
                address='北京市朝阳区柳芳南里29号',
                motto='守护每一位用户的安全与健康',
                emergency_contact_name='系统管理员',
                emergency_contact_phone='13800000000',
                emergency_contact_address='北京市朝阳区柳芳南里29号',
                password_hash=password_hash,
                password_salt=salt,
                role=Role.SUPER_ADMIN,
                status=1,
                verification_status=2,
                _is_community_worker=True,
                community_id=None,  # 暂时设为None，后续再分配
                refresh_token=None,
                refresh_token_expire=None,
                created_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                updated_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
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
                location='北京市朝阳区柳芳南里29号',
                location_lat=39.901213,
                location_lon=116.527067,
                province='北京市',
                city='北京市',
                district='朝阳区',
                street='柳芳南里',
                settings='{"checkin_enabled": true, "event_notifications": true}',
                created_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                updated_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
            )
            db.session.add(default_community)
            db.session.flush()  # 获取社区ID
            logger.info(f"默认社区'安卡大家庭'创建成功，ID: {default_community.community_id}")
        else:
            logger.info("默认社区'安卡大家庭'已存在")
            # 为已存在的社区设置缺失字段（如果为空）
            if not default_community.location:
                default_community.location = '北京市朝阳区柳芳南里29号'
            if not default_community.location_lat:
                default_community.location_lat = 39.901213
            if not default_community.location_lon:
                default_community.location_lon = 116.527067
            if not default_community.province:
                default_community.province = '北京市'
            if not default_community.city:
                default_community.city = '北京市'
            if not default_community.district:
                default_community.district = '朝阳区'
            if not default_community.street:
                default_community.street = '柳芳南里'
            if not default_community.settings:
                default_community.settings = '{"checkin_enabled": true, "event_notifications": true}'
            logger.info("已为默认社区'安卡大家庭'补充缺失字段")

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
                location='北京市海淀区中关村大街1号',
                location_lat=39.956073,
                location_lon=116.307079,
                province='北京市',
                city='北京市',
                district='海淀区',
                street='中关村大街',
                settings='{"checkin_enabled": false, "event_notifications": false, "restricted_mode": true}',
                created_at=datetime(2024, 1, 2, 0, 0, 0, tzinfo=timezone.utc),
                updated_at=datetime(2024, 1, 2, 18, 30, 0, tzinfo=timezone.utc)
            )
            db.session.add(blackhouse_community)
            db.session.flush()  # 获取社区ID
            logger.info(f"黑屋社区'{BLACKHOUSE_COMMUNITY_NAME}'创建成功，ID: {blackhouse_community.community_id}")
        else:
            logger.info(f"黑屋社区'{BLACKHOUSE_COMMUNITY_NAME}'已存在")
            # 为已存在的社区设置缺失字段（如果为空）
            if not blackhouse_community.location:
                blackhouse_community.location = '北京市海淀区中关村大街1号'
            if not blackhouse_community.location_lat:
                blackhouse_community.location_lat = 39.956073
            if not blackhouse_community.location_lon:
                blackhouse_community.location_lon = 116.307079
            if not blackhouse_community.province:
                blackhouse_community.province = '北京市'
            if not blackhouse_community.city:
                blackhouse_community.city = '北京市'
            if not blackhouse_community.district:
                blackhouse_community.district = '海淀区'
            if not blackhouse_community.street:
                blackhouse_community.street = '中关村大街'
            if not blackhouse_community.settings:
                blackhouse_community.settings = '{"checkin_enabled": false, "event_notifications": false, "restricted_mode": true}'
            logger.info(f"已为黑屋社区'{BLACKHOUSE_COMMUNITY_NAME}'补充缺失字段")

        # 检查并创建普通测试用户
        stmt = select(User).where(User.phone_number == '18122222222')
        normal_user = db.session.execute(stmt).scalar_one_or_none()

        if not normal_user:
            logger.info("开始创建普通测试用户...")
            salt = secrets.token_hex(8)
            password_hash = sha256(f"F1234567:{salt}".encode('utf-8')).hexdigest()
            phone_hash = generate_phone_hash("18122222222")

            normal_user = User(
                phone_number='18122222222',
                phone_hash=phone_hash,
                nickname='普通用户',
                name='张三',
                avatar_url='https://example.com/avatar/normal_user.png',
                work_id='EMP0001',
                address='北京市朝阳区柳芳南里30号',
                password_hash=password_hash,
                password_salt=salt,
                role=Role.SOLO,  # 普通用户角色
                status=1,
                community_id=default_community.community_id,  # 属于安卡大家庭
                created_at=datetime(2024, 1, 10, 8, 0, 0, tzinfo=timezone.utc),
                updated_at=datetime(2024, 1, 10, 8, 0, 0, tzinfo=timezone.utc)
            )
            db.session.add(normal_user)
            db.session.flush()  # 获取用户ID
            logger.info(f"普通测试用户创建成功，ID: {normal_user.user_id}")

            # 创建个人打卡规则：早上吃药
            personal_rule = CheckinRule(
                user_id=normal_user.user_id,
                community_id=None,
                rule_type='personal',
                rule_name='早上吃药',
                icon_url='https://example.com/icon/medicine.png',
                frequency_type=0,  # 每天
                time_slot_type=4,  # 早上
                custom_time=time(8, 0, 0),  # 早上 8:00
                custom_start_date=datetime(2024, 1, 10).date(),
                custom_end_date=None,
                week_days=127,  # 每天
                status=1,  # 启用
                created_at=datetime(2024, 1, 10, 8, 0, 0, tzinfo=timezone.utc),
                updated_at=datetime(2024, 1, 10, 8, 0, 0, tzinfo=timezone.utc)
            )
            db.session.add(personal_rule)
            logger.info(f"个人打卡规则'早上吃药'创建成功，规则ID: {personal_rule.rule_id}")
        else:
            logger.info(f"普通测试用户已存在，ID: {normal_user.user_id}")

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