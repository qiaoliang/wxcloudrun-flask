"""
获取社区事件统计用例
"""
import logging

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory


class GetCommunityStatsUseCase(BaseUseCase):
    """获取社区事件统计用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.community_repository = RepositoryFactory.get_community_repository()
        self.community_event_repository = RepositoryFactory.get_community_event_repository()

    def execute(self, community_id: int) -> UseCaseResult:
        """
        执行获取社区事件统计用例

        Args:
            community_id: 社区ID

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not community_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='社区ID不能为空'
                )

            # 2. 验证社区是否存在
            community = self.community_repository.find_by_id(community_id)
            if not community:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='社区不存在'
                )

            # 3. 查询未结束事件数量（状态为1-进行中）
            active_events_count = self.community_event_repository.count_by_community_id(community_id, status=1)

            # 4. 查询应援数量（未结束事件中的supporting类型事件数量）
            support_events = self.community_event_repository.find_by_community_id(
                community_id, status=1, event_type='supporting'
            )
            support_events_count = len(support_events)

            self.logger.info(f'获取社区统计成功: community_id={community_id}')

            # 5. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='获取社区统计成功',
                data={
                    'active_events': active_events_count,
                    'support_count': support_events_count
                }
            )

        except Exception as e:
            self.logger.error(f'获取社区统计失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'获取社区统计失败: {str(e)}'
            )