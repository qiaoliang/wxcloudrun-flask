"""
超级管理员和默认社区初始化模块
用于系统启动时创建必要的初始数据
"""

import logging
import secrets
import os
from hashlib import sha256
from database.models import User, Community, CommunityStaff
from database.core import get_database


def create_super_admin_and_default_community(db_core):
    """
    创建超级管理员和默认社区

    Args:
        db_core: 数据库核心实例
    """
    logger = logging.getLogger('log')
    logger.info("开始创建超级管理员和默认社区...")

    try:
        with db_core.get_session() as session:
            logger.info("数据库会话已创建")

            # 检查超级管理员是否已存在
            logger.info("检查超级管理员是否存在...")
            existing_admin = session.query(User).filter(
                User.phone_number == '13900007997'
            ).first()

            if existing_admin:
                logger.info("超级管理员已存在，跳过创建")
            else:
                logger.info("开始创建超级管理员...")
                # 创建超级管理员
                salt = secrets.token_hex(8)
                password_hash = sha256(f"Firefox0820:{salt}".encode('utf-8')).hexdigest()

                # 使用与auth.py相同的手机号哈希方法
                phone_secret = os.getenv('PHONE_ENC_SECRET', 'default_secret')
                phone_hash = sha256(f"{phone_secret}:13900007997".encode('utf-8')).hexdigest()
                
                super_admin = User(
                    wechat_openid=f"super_admin_{secrets.token_hex(16)}",  # 生成唯一openid
                    phone_number='13900007997',
                    phone_hash=phone_hash,
                    nickname='系统超级管理员',
                    name='系统超级管理员',
                    password_hash=password_hash,
                    password_salt=salt,
                    role=4,  # 社区工作人员角色
                    status=1,  # 正常状态
                    verification_status=2,  # 已通过验证
                    _is_community_worker=True
                )

                session.add(super_admin)
                session.flush()  # 获取新创建的用户ID
                logger.info(f"超级管理员创建成功，ID: {super_admin.user_id}")

            # 检查默认社区是否已存在
            logger.info("检查默认社区是否存在...")
            existing_community = session.query(Community).filter(
                Community.name == '安卡大家庭'
            ).first()

            if existing_community:
                logger.info("默认社区'安卡大家庭'已存在，跳过创建")

                # 确保超级管理员是社区主管
                admin_user = session.query(User).filter(
                    User.phone_number == '13900007997'
                ).first()

                if admin_user:
                    existing_staff = session.query(CommunityStaff).filter(
                        CommunityStaff.community_id == existing_community.community_id,
                        CommunityStaff.user_id == admin_user.user_id,
                        CommunityStaff.role == 'manager'
                    ).first()

                    if not existing_staff:
                        # 设置为社区主管
                        staff_relation = CommunityStaff(
                            community_id=existing_community.community_id,
                            user_id=admin_user.user_id,
                            role='manager'
                        )
                        session.add(staff_relation)
                        logger.info(f"超级管理员设置为社区主管，社区ID: {existing_community.community_id}")
            else:
                logger.info("开始创建默认社区...")
                # 获取或创建超级管理员（用于关联）
                admin_user = session.query(User).filter(
                    User.phone_number == '13900007997'
                ).first()

                if not admin_user:
                    logger.error("超级管理员不存在，无法创建默认社区")
                    raise Exception("超级管理员不存在，无法创建默认社区")

                # 创建默认社区
                default_community = Community(
                    name='安卡大家庭',
                    description='系统默认社区，新注册用户自动加入',
                    creator_user_id=admin_user.user_id,
                    status=1,  # 启用状态
                    is_default=True
                )

                session.add(default_community)
                session.flush()  # 获取新创建的社区ID
                logger.info(f"默认社区'安卡大家庭'创建成功，ID: {default_community.community_id}")

                # 设置超级管理员为社区主管
                staff_relation = CommunityStaff(
                    community_id=default_community.community_id,
                    user_id=admin_user.user_id,
                    role='manager'
                )
                session.add(staff_relation)
                logger.info(f"超级管理员设置为社区主管，社区ID: {default_community.community_id}")

            session.commit()
            logger.info("超级管理员和默认社区初始化完成")

    except Exception as e:
        logger.error(f"创建超级管理员和默认社区失败: {str(e)}")
        raise