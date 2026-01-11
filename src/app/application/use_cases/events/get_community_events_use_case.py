"""
获取社区事件列表用例
"""
import logging
from typing import Optional

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory


class GetCommunityEventsUseCase(BaseUseCase):
    """获取社区事件列表用例"""

    def __init__(self):
        super().__init__()
        self.community_event_repository = RepositoryFactory.get_community_event_repository()
        self.community_repository = RepositoryFactory.get_community_repository()

    def execute(
        self,
        community_id: int,
        event_type: Optional[str] = None,
        status: Optional[int] = None,
        page: int = 1,
        page_size: int = 20
    ) -> UseCaseResult:
        """
        执行获取社区事件列表用例

        Args:
            community_id: 社区ID
            event_type: 事件类型（call_for_help, supporting）
            status: 事件状态（1=pending, 2=resolved, 3=cancelled）
            page: 页码
            page_size: 每页数量

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

            if page < 1:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='页码必须大于0'
                )

            if page_size < 1 or page_size > 100:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='每页数量必须在1-100之间'
                )

            # 2. 验证社区是否存在
            community = self.community_repository.find_by_id(community_id)
            if not community:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='社区不存在'
                )

            # 3. 查询社区事件
            events = self.community_event_repository.find_by_community_id(community_id)

            # 4. 筛选事件类型
            if event_type:
                events = [event for event in events if event.event_type == event_type]

            # 5. 筛选事件状态
            if status is not None:
                events = [event for event in events if event.status == status]

            # 6. 按创建时间倒序排列
            events.sort(key=lambda x: x.created_at if x.created_at else None, reverse=True)

            # 7. 分页处理
            total = len(events)
            start = (page - 1) * page_size
            end = start + page_size
            paged_events = events[start:end]

            # 8. 构造响应数据
            event_list = []
            for event in paged_events:
                event_list.append({
                    'event_id': event.event_id,
                    'community_id': event.community_id,
                    'target_user_id': event.target_user_id,
                    'event_type': event.event_type,
                    'status': event.status,
                    'location': event.location,
                    'description': event.description,
                    'created_at': event.created_at.isoformat() if event.created_at else None,
                    'updated_at': event.updated_at.isoformat() if event.updated_at else None,
                    'closed_at': event.closed_at.isoformat() if event.closed_at else None
                })

            response_data = {
                'events': event_list,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }

            self.logger.info(f'获取社区事件列表成功: community_id={community_id}, total={total}')

            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='获取社区事件列表成功',
                data=response_data
            )

        except Exception as e:
            self.logger.error(f'获取社区事件列表失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'获取社区事件列表失败: {str(e)}'
            )