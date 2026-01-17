"""
获取可加入社区列表用例
"""
import logging
from sqlalchemy.orm import joinedload

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.domain.repositories.community_repository import CommunityRepository


class GetAvailableCommunitiesUseCase(BaseUseCase):
    """获取可加入社区列表用例"""

    def __init__(self):
        super().__init__()
        self.community_repository = RepositoryFactory.get_community_repository()
        self.logger = logging.getLogger(__name__)

    def execute(self, user_id: int = None) -> UseCaseResult:
        """
        执行获取可加入社区列表用例

        Args:
            user_id: 用户ID（可选，用于过滤已加入的社区）

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 查询所有社区
            stmt = db.session.execute(
                db.select(Community)
                .where(Community.status == 1)  # 只返回正常状态的社区
                .order_by(Community.created_at.desc())
            )
            communities = stmt.scalars().all()

            # 2. 构造社区列表
            communities_data = []
            for community in communities:
                # 如果提供了 user_id，检查用户是否已加入该社区
                is_member = False
                if user_id:
                    # 这里可以添加逻辑检查用户是否已加入该社区
                    pass

                communities_data.append({
                    'community_id': community.community_id,
                    'name': community.name,
                    'description': community.description,
                    'address': community.address,
                    'contact_phone': community.contact_phone,
                    'status': community.status,
                    'is_member': is_member,
                    'created_at': community.created_at.isoformat() if community.created_at else None
                })

            self.logger.info(f'获取可加入社区列表成功: count={len(communities_data)}')

            # 3. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='获取社区列表成功',
                data={'communities': communities_data, 'count': len(communities_data)}
            )

        except Exception as e:
            self.logger.error(f'获取可加入社区列表失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'获取社区列表失败: {str(e)}'
            )