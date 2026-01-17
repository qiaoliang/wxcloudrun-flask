"""
添加事件消息用例
"""
import logging
from datetime import datetime
from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.domain.events.event_bus import EventBus, event_bus
from app.domain.events.community_events import EventMessageAddedEvent
from app.domain.entities.community_event_entity import CommunityEventEntity
from app.domain.entities.event_message_entity import EventMessageEntity
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

    def execute(
        self,
        event_id: int,
        user_id: int,
        message: str = '',
        message_type: str = 'text',
        media_url: str = None,
        message_tags: list = None
    ) -> UseCaseResult:
        """
        执行添加事件消息用例

        Args:
            event_id: 事件ID
            user_id: 用户ID
            message: 消息内容
            message_type: 消息类型（text/image/voice）
            media_url: 媒体文件URL（语音或图片）
            message_tags: 消息标签列表

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not event_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='事件ID不能为空'
                )

            if not user_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='发送者ID不能为空'
                )

            # 验证至少有一个内容：文字、媒体或标签
            message_stripped = message.strip() if message else ''
            has_content = bool(message_stripped)
            has_media = bool(media_url)
            has_tags = bool(message_tags)

            if not has_content and not has_media and not has_tags:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='请至少提供文字内容、媒体文件或快捷指令'
                )

            # 如果提供了 media_url 但没有指定 message_type，则自动推断
            if media_url and message_type == 'text':
                media_url_lower = media_url.lower()
                if media_url_lower.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')):
                    message_type = 'image'
                elif media_url_lower.endswith(('.mp3', '.wav', '.m4a', '.aac', '.ogg')):
                    message_type = 'voice'

            # 2. 验证用户是否存在
            sender = self.user_repository.find_by_id(user_id)
            if not sender:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='发送者不存在'
                )

            # 3. 查找事件
            event = self.community_event_repository.find_by_id(event_id)
            if not event:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='事件不存在'
                )

            # 3.5 检查事件状态，已关闭的事件不能添加消息
            if event.status != 1:  # 1=进行中，2=已解决，3=已取消
                return UseCaseResult(
                    status=UseCaseStatus.BUSINESS_ERROR,
                    message='事件已关闭，无法添加消息'
                )

            # 4. 创建事件聚合根并添加消息
            event_entity = CommunityEventEntity(event)
            event_aggregate = CommunityEventAggregate(event_entity)

            # 在聚合根中添加消息（业务规则在聚合根内验证）
            try:
                # 先创建 EventMessage 对象
                event_message_obj = EventMessage(
                    event_id=event_id,
                    sender_id=user_id,
                    message_content=message_stripped,
                    message_type=message_type,
                    media_url=media_url,
                    message_tags=message_tags,
                    status=1,
                    created_at=datetime.now()
                )
                message_entity = EventMessageEntity(event_message_obj)
                event_aggregate.add_message(message_entity)
            except ValueError as e:
                return UseCaseResult(
                    status=UseCaseStatus.BUSINESS_ERROR,
                    message=str(e)
                )

            # 5. 创建事件消息
            event_message = EventMessage(
                event_id=event_id,
                    sender_id=user_id,
                    message_content=message_stripped,
                    message_type=message_type,
                    media_url=media_url,
                    message_tags=message_tags,
                    status=1,
                    created_at=datetime.now()
            )

            saved_message = self.event_message_repository.save(event_message)

            self.logger.info(f'添加事件消息成功: event_id={event_id}, user_id={user_id}, type={message_type}')

            # 6. 发布领域事件
            event_message_added = EventMessageAddedEvent(
                event_id=event_id,
                sender_id=user_id,
                message_type=message_type,
                message_content=message_stripped,
                media_url=media_url,
                message_tags=message_tags
            )
            event_bus.publish(event_message_added)

            # 7. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='添加消息成功',
                data={
                    'message_id': saved_message.message_id,
                    'message_type': saved_message.message_type,
                    'media_url': saved_message.media_url,
                    'message_tags': saved_message.message_tags or []
                }
            )

        except Exception as e:
            self.logger.error(f'添加事件消息失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'添加消息失败: {str(e)}'
            )