"""
获取社区事件统计用例
"""
import logging
from sqlalchemy import select, func

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from database.flask_models import db, CommunityEvent


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
            stmt_active = select(func.count()).select_from(CommunityEvent).where(
                CommunityEvent.community_id == community_id,
                CommunityEvent.status == 1
            )
            active_events_count = db.session.execute(stmt_active).scalar()

            # 4. 查询应援数量（未结束事件中的supporting类型事件数量）
            stmt_support = select(func.count()).select_from(CommunityEvent).where(
                CommunityEvent.community_id == community_id,
                CommunityEvent.status == 1,
                CommunityEvent.event_type == 'supporting'
            )
            support_events_count = db.session.execute(stmt_support).scalar()

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