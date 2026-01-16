"""
添加事件消息用例
"""
import logging
from datetime import datetime
from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.domain.events.event_bus import EventBus
from app.domain.entities.community_event_entity import CommunityEventEntity
from app.domain.aggregates.community_event_aggregate import CommunityEventAggregate
from database.flask_models import EventMessage


class AddEventMessageUseCase(BaseUseCase):
    """添加事件消息用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.user_repository = RepositoryFactory.get_user_repository()
        self.community_event_repository = RepositoryFactory.get_community_event_repository()
        self.event_message_repository = RepositoryFactory.get_event_message_repository()
        self.event_bus = EventBus()

    def execute(self, event_id: int, user_id: int, message: str, message_type: str = 'text') -> UseCaseResult:
        """
        执行添加事件消息用例

        Args:
            event_id: 事件ID
            user_id: 用户ID
            message: 消息内容
            message_type: 消息类型（text/image/voice）

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not event_id or not user_id or not message:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='参数不能为空'
                )

            # 2. 验证用户是否存在
            sender = self.user_repository.find_by_id(user_id)
            if not sender:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='用户不存在'
                )

            # 3. 查找事件
            event = self.community_event_repository.find_by_id(event_id)
            if not event:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='事件不存在'
                )

            # 4. 创建事件聚合根并添加消息
            event_entity = CommunityEventEntity(event)
            event_aggregate = CommunityEventAggregate(event_entity, self.event_bus)

            # 在聚合根中添加消息（业务规则在聚合根内验证）
            try:
                event_aggregate.add_message(
                    sender_id=user_id,
                    message=message,
                    message_type=message_type
                )
            except ValueError as e:
                return UseCaseResult(
                    status=UseCaseStatus.BUSINESS_ERROR,
                    message=str(e)
                )

            # 5. 创建事件消息
            event_message = EventMessage(
                event_id=event_id,
                sender_id=user_id,
                message_content=message,
                message_type=message_type,
                status=1,
                created_at=datetime.now()
            )

            saved_message = self.event_message_repository.save(event_message)

            self.logger.info(f'添加事件消息成功: event_id={event_id}, user_id={user_id}')

            # 6. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='添加消息成功',
                data={'message_id': saved_message.message_id}
            )

        except Exception as e:
            self.logger.error(f'添加事件消息失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'添加消息失败: {str(e)}'
            )