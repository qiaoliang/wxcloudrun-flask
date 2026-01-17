"""
获取可管理社区列表用例
"""
import logging
from sqlalchemy import and_, or_
from sqlalchemy.orm import joinedload

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.domain.repositories.community_staff_repository import CommunityStaffRepository
from app.domain.repositories.community_repository import CommunityRepository


class GetManagedCommunitiesUseCase(BaseUseCase):
    """获取可管理社区列表用例"""

    def __init__(self):
        super().__init__()
        self.community_staff_repo = CommunityStaffRepository()
        self.community_repository = RepositoryFactory.get_community_repository()
        self.logger = logging.getLogger(__name__)

    def execute(self, user_id: int, limit: int = 7) -> UseCaseResult:
        """
        执行获取可管理社区列表用例

        Args:
            user_id: 用户ID
            limit: 返回社区数量限制

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not user_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='用户ID不能为空'
                )

            # 2. 查询用户可管理的社区
            # 用户可以管理的社区包括：
            # - 用户是工作人员的社区
            # - 用户是成员的社区（如果是管理员）
            
            # 查询用户作为工作人员的社区
            stmt_staff = db.session.execute(
                db.select(Community)
                .join(CommunityStaff)
                .where(CommunityStaff.user_id == user_id)
                .where(Community.status == 1)
                .order_by(Community.created_at.desc())
            )
            staff_communities = stmt_staff.scalars().all()
            
            # 构造社区列表
            communities_data = []
            for community in staff_communities:
                communities_data.append({
                    'community_id': community.community_id,
                    'name': community.name,
                    'description': community.description,
                    'address': community.address,
                    'contact_phone': community.contact_phone,
                    'status': community.status,
                    'role': 'staff',
                    'created_at': community.created_at.isoformat() if community.created_at else None
                })

            self.logger.info(f'获取可管理社区列表成功: user_id={user_id}, count={len(communities_data)}')

            # 3. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='获取可管理社区列表成功',
                data={'communities': communities_data, 'count': len(communities_data)}
            )

        except Exception as e:
            self.logger.error(f'获取可管理社区列表失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'获取可管理社区列表失败: {str(e)}'
            )