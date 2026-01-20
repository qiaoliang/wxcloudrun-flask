"""
获取所有社区列表用例（超级管理员专用）
已废弃：请使用 GetCommunitiesUseCase 并传入 type='all'
"""
import logging

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.application.use_cases.community.get_communities_use_case import GetCommunitiesUseCase


class GetAllCommunitiesUseCase(BaseUseCase):
    """获取所有社区列表用例（超级管理员专用）- 已废弃"""

    def __init__(self):
        super().__init__()
        self.get_communities_use_case = GetCommunitiesUseCase()
        self.logger = logging.getLogger(__name__)

    def execute(self, user_id: int = None) -> UseCaseResult:
        """
        执行获取所有社区列表用例

        Args:
            user_id: 用户ID（用于权限检查）

        Returns:
            UseCaseResult: 执行结果，包含社区对象列表
        """
        try:
            # 调用新的统一 UseCase
            params = {
                'type': 'all',
                'user_id': user_id,
                'limit': 1000
            }

            result = self.get_communities_use_case.execute(params)

            # 转换结果格式以保持向后兼容
            if result.is_success:
                # 返回社区对象列表（供 FormatCommunityInfoUseCase 使用）
                # 注意：这里需要从格式化后的数据中提取原始社区对象
                # 由于新 UseCase 返回的是格式化后的数据，我们需要调整
                # 为了保持向后兼容，我们暂时返回格式化后的数据
                return result
            else:
                return result

        except Exception as e:
            self.logger.error(f'获取所有社区列表失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'获取所有社区列表失败: {str(e)}'
            )
