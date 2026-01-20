"""
获取可管理社区列表用例
已废弃：请使用 GetCommunitiesUseCase 并传入 type='managed'
"""
import logging

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.application.use_cases.community.get_communities_use_case import GetCommunitiesUseCase


class GetManagedCommunitiesUseCase(BaseUseCase):
    """获取可管理社区列表用例 - 已废弃"""

    def __init__(self):
        super().__init__()
        self.get_communities_use_case = GetCommunitiesUseCase()
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

            # 2. 调用新的统一 UseCase
            params = {
                'type': 'managed',
                'user_id': user_id,
                'limit': limit
            }

            result = self.get_communities_use_case.execute(params)

            return result

        except Exception as e:
            self.logger.error(f'获取可管理社区列表失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'获取可管理社区列表失败: {str(e)}'
            )