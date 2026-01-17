"""
获取管理员列表用例
"""
import logging

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.domain.repositories.user_repository import UserRepository
from app.domain.repositories.community_staff_repository import CommunityStaffRepository
from app.domain.repositories.community_repository import CommunityRepository
from app.shared.constants.roles import Role, STAFF_ROLE_MANAGER

logger = logging.getLogger(__name__)


class GetAdminListUseCase(BaseUseCase):
    """获取管理员列表用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.user_repo = UserRepository()
        self.community_staff_repo = CommunityStaffRepository()
        self.community_repo = CommunityRepository()

    def execute(self) -> UseCaseResult:
        """
        执行获取管理员列表用例

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 查询所有超级管理员
            super_admins = self.user_repo.find_super_admins()

            # 2. 查询所有社区主管
            manager_records = self.community_staff_repo.find_active_managers_with_details()

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