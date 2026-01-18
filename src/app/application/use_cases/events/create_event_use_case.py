"""
from app.shared.utils.transaction import transactional
创建社区事件用例
"""
import logging
from datetime import datetime
from typing import Optional

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.domain.events.event_bus import EventBus
from app.domain.events.community_events import EventCreatedEvent
from database.flask_models import CommunityEvent


class CreateEventUseCase(BaseUseCase):
    """创建社区事件用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.user_repository = RepositoryFactory.get_user_repository()
        self.community_repository = RepositoryFactory.get_community_repository()
        self.community_event_repository = RepositoryFactory.get_community_event_repository()
        self.event_bus = EventBus()

    @transactional


    def execute(
        self,
        user_id: int,
        community_id: int,
        title: str,
        description: str = "",
        event_type: str = "call_for_help",
        location: str = "",
        target_user_id: Optional[int] = None
    ) -> UseCaseResult:
        """
        执行创建事件用例

        Args:
            user_id: 创建者用户ID
            community_id: 社区ID
            title: 事件标题
            description: 事件描述
            event_type: 事件类型
            location: 事件地点
            target_user_id: 目标用户ID

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not title or not title.strip():
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='事件标题不能为空'
                )

            if event_type not in ['call_for_help', 'supporting']:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='无效的事件类型'
                )

            # 2. 验证用户是否存在
            user = self.user_repository.find_by_id(user_id)
            if not user:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='用户不存在'
                )

            # 3. 验证社区是否存在
            community = self.community_repository.find_by_id(community_id)
            if not community:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='社区不存在'
                )

            # 4. 验证用户是否属于该社区
            if user.community_id != community_id:
                return UseCaseResult(
                    status=UseCaseStatus.FORBIDDEN,
                    message='用户不属于该社区'
                )

            # 5. 检查是否为一键求助类型
            if event_type == 'call_for_help' and target_user_id:
                # 检查该用户是否已有进行中的一键求助事件
                existing_events = self.community_event_repository.find_by_target_user_id(
                    target_user_id,
                    status=1  # 进行中
                )

                for existing_event in existing_events:
                    if existing_event.event_type == 'call_for_help':
                        self.logger.warning(f"用户{target_user_id}已有进行中的一键求助事件{existing_event.event_id}")
                        return UseCaseResult(
                            status=UseCaseStatus.BUSINESS_ERROR,
                            message='您已有进行中的求助事件，请先关闭或等待工作人员处理'
                        )

            # 6. 创建事件
            event = CommunityEvent(
                community_id=community_id,
                title=title,
                description=description,
                event_type=event_type,
                location=location,
                target_user_id=target_user_id,
                created_by=user_id,
                status=1,  # 进行中
                created_at=datetime.now()
            )

            saved_event = self.community_event_repository.save(event)

            self.logger.info(f"用户{user_id}在社区{community_id}创建了事件{saved_event.event_id}")

            # 7. 发布领域事件
            self.event_bus.publish(EventCreatedEvent(
                event_id=saved_event.event_id,
                community_id=community_id,
                creator_id=user_id,
                event_type=event_type,
                title=title,
                target_user_id=target_user_id
            ))

            # 8. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='事件创建成功',
                data={
                    'event': {
                        'event_id': saved_event.event_id,
                        'community_id': saved_event.community_id,
                        'title': saved_event.title,
                        'event_type': saved_event.event_type,
                        'status': saved_event.status,
                        'target_user_id': saved_event.target_user_id,
                        'created_by': saved_event.created_by,
                        'created_at': saved_event.created_at.isoformat() if saved_event.created_at else None
                    }
                }
            )

        except ValueError as e:
            self.logger.error(f'创建事件失败: {str(e)}')
            return UseCaseResult(
                status=UseCaseStatus.BUSINESS_ERROR,
                message=str(e)
            )
        except Exception as e:
            self.logger.error(f'创建事件失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'创建事件失败: {str(e)}'
            )