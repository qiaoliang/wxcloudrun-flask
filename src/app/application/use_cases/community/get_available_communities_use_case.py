"""
获取可加入社区列表用例
已废弃：请使用 GetCommunitiesUseCase 并传入 type='available'
"""
import logging

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.application.use_cases.community.get_communities_use_case import GetCommunitiesUseCase


class GetAvailableCommunitiesUseCase(BaseUseCase):
    """获取可加入社区列表用例 - 已废弃"""

    def __init__(self):
        super().__init__()
        self.get_communities_use_case = GetCommunitiesUseCase()
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
            # 调用新的统一 UseCase
            params = {
                'type': 'available',
                'user_id': user_id,
                'limit': 1000
            }

            result = self.get_communities_use_case.execute(params)

            return result

        except Exception as e:
            self.logger.error(f'获取可加入社区列表失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'获取社区列表失败: {str(e)}'
            )