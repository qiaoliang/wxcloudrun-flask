"""
获取社区未处理的求助事件用例
"""
import logging
from sqlalchemy import select

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from database.flask_models import db, CommunityEvent


class GetPendingEventsUseCase(BaseUseCase):
    """获取社区未处理的求助事件用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.community_repository = RepositoryFactory.get_community_repository()
        self.community_event_repository = RepositoryFactory.get_community_event_repository()

    def execute(self, community_id: int) -> UseCaseResult:
        """
        执行获取社区未处理的求助事件用例

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

            # 3. 查询未处理的call_for_help类型事件
            stmt = select(CommunityEvent).where(
                CommunityEvent.community_id == community_id,
                CommunityEvent.event_type == 'call_for_help',
                CommunityEvent.status == 1
            ).order_by(CommunityEvent.created_at.desc())

            events = db.session.execute(stmt).scalars().all()

            # 4. 构造响应数据
            event_list = []
            for event in events:
                event_list.append({
                    'event_id': event.event_id,
                    'community_id': event.community_id,
                    'target_user_id': event.target_user_id,
                    'event_type': event.event_type,
                    'status': event.status,
                    'location': event.location,
                    'description': event.description,
                    'created_at': event.created_at.isoformat() if event.created_at else None,
                    'updated_at': event.updated_at.isoformat() if event.updated_at else None
                })

            self.logger.info(f'获取未处理事件成功: community_id={community_id}, count={len(event_list)}')

            # 5. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='获取未处理事件成功',
                data={
                    'events': event_list,
                    'count': len(event_list)
                }
            )

        except Exception as e:
            self.logger.error(f'获取未处理事件失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'获取未处理事件失败: {str(e)}'
            )