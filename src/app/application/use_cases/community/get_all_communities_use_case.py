"""
获取所有社区列表用例（超级管理员专用）
"""
import logging

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.domain.repositories.community_repository import CommunityRepository


class GetAllCommunitiesUseCase(BaseUseCase):
    """获取所有社区列表用例（超级管理员专用）"""

    def __init__(self):
        super().__init__()
        self.community_repository = RepositoryFactory.get_community_repository()
        self.logger = logging.getLogger(__name__)

    def execute(self) -> UseCaseResult:
        """
        执行获取所有社区列表用例

        Returns:
            UseCaseResult: 执行结果，包含社区对象列表
        """
        try:
            # 使用 Repository 获取所有社区
            communities = self.community_repo.get_all()

            self.logger.info(f'获取所有社区列表成功，共 {len(communities)} 个社区')

            # 返回社区对象列表（供 FormatCommunityInfoUseCase 使用）
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='获取所有社区列表成功',
                data={'communities': communities}
            )

        except Exception as e:
            self.logger.error(f'获取所有社区列表失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'获取所有社区列表失败: {str(e)}'
            )
