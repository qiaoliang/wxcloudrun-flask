"""
获取社区工作人员列表用例（重构后 - 符合DDD架构）

重构要点：
- 移除直接导入 database.flask_models 中的 db, User, CommunityStaff
- 使用Repository接口访问数据，符合依赖倒置原则（DIP）
- 所有数据库操作通过Repository抽象层
"""

import logging
from typing import Optional

from app.application.use_cases.base import BaseUseCase, UseCaseResult, UseCaseStatus
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.shared.constants.roles import STAFF_ROLE_MANAGER, STAFF_ROLE_STAFF

logger = logging.getLogger(__name__)


class GetCommunityStaffListUseCase(BaseUseCase):
    """获取社区工作人员列表用例"""

    def __init__(self):
        """
        初始化用例，注入所有需要的Repository

        符合依赖倒置原则：依赖Repository接口，而非具体实现
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        # ✅ 通过RepositoryFactory获取Repository接口
        self.user_repository = RepositoryFactory.get_user_repository()
        self.staff_repository = RepositoryFactory.get_community_staff_repository()

    def execute(
        self,
        community_id: int,
        role: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> UseCaseResult:
        """
        获取社区工作人员列表

        Args:
            community_id: 社区ID
            role: 角色筛选 ('manager', 'staff' 或 None 表示全部)
            page: 页码，从1开始
            limit: 每页数量

        Returns:
            UseCaseResult: 包含工作人员列表和分页信息
        """
        try:
            # 1. 参数验证
            validation_result = self._validate_params(community_id, role, page, limit)
            if not validation_result.is_success:
                return validation_result

            # 2. 获取工作人员列表
            # ✅ 使用Repository代替 db.session.execute(select(CommunityStaff)...)
            if role and role != 'all':
                if role == 'manager':
                    staff_list = self.staff_repository.find_by_community_and_role(
                        community_id, STAFF_ROLE_MANAGER, include_removed=False
                    )
                elif role == 'staff':
                    staff_list = self.staff_repository.find_by_community_and_role(
                        community_id, STAFF_ROLE_STAFF, include_removed=False
                    )
                else:
                    staff_list = []
            else:
                staff_list = self.staff_repository.find_by_community_id(
                    community_id, include_removed=False
                )

            # 3. 获取总数
            # ✅ 使用Repository获取总数
            if role and role != 'all':
                if role == 'manager':
                    total_count = self.staff_repository.count_by_community_id(
                        community_id, STAFF_ROLE_MANAGER
                    )
                elif role == 'staff':
                    total_count = self.staff_repository.count_by_community_id(
                        community_id, STAFF_ROLE_STAFF
                    )
                else:
                    total_count = 0
            else:
                total_count = self.staff_repository.count_by_community_id(community_id)

            # 4. 分页处理
            # 手动实现分页
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            paginated_staff_list = staff_list[start_idx:end_idx]

            # 5. 构造返回数据
            staff_data = []
            for staff in paginated_staff_list:
                # ✅ 使用Repository代替 db.session.get(User, staff.user_id)
                user = self.user_repository.find_by_id(staff.user_id)
                if user:
                    staff_info = {
                        'staff_id': staff.id,
                        'user_id': user.user_id,
                        'wechat_openid': user.wechat_openid,
                        'phone_number': user.phone_number,
                        'nickname': user.nickname,
                        'name': user.name,
                        'avatar_url': user.avatar_url,
                        'role': staff.role,
                        'added_at': staff.added_at.isoformat() if staff.added_at else None
                    }
                    staff_data.append(staff_info)

            # 计算分页信息
            total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1
            has_more = page < total_pages

            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='获取工作人员列表成功',
                data={
                    'staff': staff_data,
                    'pagination': {
                        'page': page,
                        'limit': limit,
                        'total': total_count,
                        'total_pages': total_pages,
                        'has_more': has_more
                    }
                }
            )

        except Exception as e:
            logger.error(f'获取社区工作人员列表失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'获取工作人员列表失败: {str(e)}'
            )

    def _validate_params(
        self,
        community_id: int,
        role: Optional[str],
        page: int,
        limit: int
    ) -> UseCaseResult:
        """验证参数"""
        if not community_id:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='缺少社区ID'
            )

        # 验证role参数
        if role and role not in ['all', 'manager', 'staff']:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message=f'无效的角色参数，支持的角色: all, manager, staff'
            )

        # 验证分页参数
        if page < 1:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='页码必须大于0'
            )

        if limit < 1 or limit > 100:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='每页数量必须在1-100之间'
            )

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message='参数验证通过'
        )
