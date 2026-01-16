"""
获取管理员列表用例
"""
import logging
from sqlalchemy import select

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from database.flask_models import db, User, CommunityStaff, Community
from app.shared.constants.roles import Role, STAFF_ROLE_MANAGER

logger = logging.getLogger(__name__)


class GetAdminListUseCase(BaseUseCase):
    """获取管理员列表用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

    def execute(self) -> UseCaseResult:
        """
        执行获取管理员列表用例

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 查询所有超级管理员
            stmt_super_admin = select(User).where(User.role == Role.SUPER_ADMIN)
            super_admins = db.session.execute(stmt_super_admin).scalars().all()

            # 2. 查询所有社区主管
            stmt_managers = select(CommunityStaff, User, Community).join(
                User, CommunityStaff.user_id == User.user_id
            ).join(
                Community, CommunityStaff.community_id == Community.community_id
            ).where(
                CommunityStaff.role == STAFF_ROLE_MANAGER,
                CommunityStaff.removed_at.is_(None)
            )
            manager_records = db.session.execute(stmt_managers).all()

            # 3. 构建结果列表
            admin_list = []

            # 添加超级管理员
            for admin in super_admins:
                admin_list.append({
                    'user_id': admin.user_id,
                    'nickname': admin.nickname,
                    'avatar_url': admin.avatar_url,
                    'phone_number': admin.phone_number,
                    'role': 'super_admin',
                    'role_name': '超级管理员',
                    'community_name': '全部社区'
                })

            # 添加社区主管
            for staff, user, community in manager_records:
                admin_list.append({
                    'user_id': user.user_id,
                    'nickname': user.nickname,
                    'avatar_url': user.avatar_url,
                    'phone_number': user.phone_number,
                    'role': 'manager',
                    'role_name': '社区主管',
                    'community_id': community.community_id,
                    'community_name': community.name
                })

            logger.info(f'获取管理员列表成功: 共{len(admin_list)}个管理员')

            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='获取管理员列表成功',
                data={'admins': admin_list}
            )

        except Exception as e:
            logger.error(f'获取管理员列表失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'获取管理员列表失败: {str(e)}'
            )