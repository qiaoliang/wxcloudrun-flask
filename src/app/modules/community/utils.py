"""
社区模块工具函数
包含权限检查和格式化等辅助函数
"""

import logging
from flask import current_app
from sqlalchemy import select, func, not_
from database.flask_models import db, User, CommunityStaff

app_logger = logging.getLogger('log')


def _check_superadmin_permission(user):
    """检查用户是否为超级系统管理员"""
    if not user or user.role != 4:  # 4是超级管理员
        current_app.logger.warning(f'用户 {user.user_id if user else None} 无超级管理员权限')
        from app.shared import make_err_response
        return make_err_response({}, '无权限访问')
    return None


def _format_community_info(community, include_worker_stats=False):
    """
    格式化社区信息

    Args:
        community: Community对象
        include_worker_stats: 是否包含工作人员统计信息

    Returns:
        dict: 格式化后的社区信息
    """
    # 获取创建者信息
    creator = None
    if community.creator_id:
        creator_user = db.session.get(User, community.creator_id)
        if creator_user:
            creator = {
                'user_id': creator_user.user_id,
                'nickname': creator_user.nickname,
                'avatar_url': creator_user.avatar_url
            }

    # 获取主管信息
    manager = None
    current_app.logger.info(f'_format_community_info - 社区{community.community_id}的manager_id: {community.manager_id}')
    if community.manager_id:
        manager_user = db.session.get(User, community.manager_id)
        if manager_user:
            manager = {
                'user_id': manager_user.user_id,
                'nickname': manager_user.nickname,
                'avatar_url': manager_user.avatar_url
            }
            current_app.logger.info(f'_format_community_info - 成功获取主管信息: {manager}')
        else:
            current_app.logger.warning(f'_format_community_info - manager_id={community.manager_id}对应的用户不存在')
    else:
        current_app.logger.info(f'_format_community_info - 社区{community.community_id}未设置主管')

    # 获取工作人员数量统计
    manager_count = 0
    staff_count = 0
    worker_count = 0
    user_count = 0  # 普通成员数量（不包括工作人员）
    if include_worker_stats:
        # 使用 SQLAlchemy 2.0 的 select() 语句
        from sqlalchemy import func

        # 统计主管
        stmt_manager = select(func.count()).select_from(CommunityStaff).where(
            CommunityStaff.community_id == community.community_id,
            CommunityStaff.role == 'manager'  # 社区主管
        )
        manager_count = db.session.execute(stmt_manager).scalar()

        # 只统计专员（不包括主管）
        stmt_staff = select(func.count()).select_from(CommunityStaff).where(
            CommunityStaff.community_id == community.community_id,
            CommunityStaff.role == 'staff'  # 社区专员
        )
        staff_count = db.session.execute(stmt_staff).scalar()
        worker_count = manager_count + staff_count  # 工作人员总数 = 主管 + 专员

        # 获取所有工作人员的用户ID列表
        stmt_all_staff = select(CommunityStaff).where(
            CommunityStaff.community_id == community.community_id,
            CommunityStaff.removed_at.is_(None)
        )
        staff_user_ids = [s.user_id for s in db.session.execute(stmt_all_staff).scalars().all()]

        # 统计普通成员（不包括工作人员）
        if staff_user_ids:
            # 使用 SQLAlchemy 2.0 的 select() 语句
            from sqlalchemy import not_
            stmt_users = select(func.count()).select_from(User).where(
                User.community_id == community.community_id,
                not_(User.user_id.in_(staff_user_ids))
            )
            user_count = db.session.execute(stmt_users).scalar()
        else:
            # 如果没有工作人员，统计所有社区用户
            # 使用 SQLAlchemy 2.0 的 select() 语句
            stmt = select(func.count()).select_from(User).where(User.community_id == community.community_id)
            user_count = db.session.execute(stmt).scalar()

    return {
        'community_id': community.community_id,
        'name': community.name,
        'description': community.description,
        'location': community.location or '',
        'location_lat': community.location_lat,
        'location_lon': community.location_lon,
        'creator_id': community.creator_id,
        'creator': creator,
        'manager_id': community.manager_id,
        'manager': manager,
        'manager_name': manager['nickname'] if manager else None,  # 主管昵称（用于前端显示）
        'status': community.status,
        'is_default': community.is_default,
        'is_blackhouse': community.is_blackhouse,
        'created_at': community.created_at.isoformat() if community.created_at else None,
        'updated_at': community.updated_at.isoformat() if community.updated_at else None,
        'manager_count': manager_count,  # 主管数量
        'worker_count': worker_count,  # 工作人员总数（主管+专员）
        'staff_count': staff_count,  # 专员数量（不包括主管）
        'user_count': user_count  # 普通成员数量（不包括工作人员）
    }