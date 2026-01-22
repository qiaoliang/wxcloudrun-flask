"""
获取社区成员列表用例
"""

from app.application.use_cases.base import BaseUseCase, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.domain.repositories.user_repository import UserRepository


class GetCommunityMembersUseCase(BaseUseCase):
    """获取社区成员列表用例"""

    def __init__(self):
        super().__init__()
        self.user_repository = RepositoryFactory.get_user_repository()

    def execute(self, community_id: int, page: int = 1, per_page: int = 20) -> UseCaseResult:
        """
        获取社区成员列表

        Args:
            community_id: 社区ID
            page: 页码
            per_page: 每页数量

        Returns:
            UseCaseResult: 包含成员列表和总数
        """
        try:
            if not community_id:
                return UseCaseResult.fail("社区ID不能为空")

            # 使用Repository获取成员列表
            members_data, total = self.user_repository.get_community_members_paginated(
                community_id, page, per_page
            )

            return UseCaseResult.success({
                'members': members_data,
                'total': total,
                'page': page,
                'per_page': per_page
            }, "获取成员列表成功")

        except Exception as e:
            return UseCaseResult.fail(f"获取成员列表失败: {str(e)}")