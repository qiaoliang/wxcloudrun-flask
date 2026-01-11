"""
添加事件消息用例
"""
import logging
from typing import Optional, List

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from database.flask_models import EventMessage


class AddEventMessageUseCase(BaseUseCase):
    """添加事件消息用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.community_event_repository = RepositoryFactory.get_community_event_repository()
        self.event_message_repository = RepositoryFactory.get_event_message_repository()
        self.user_repository = RepositoryFactory.get_user_repository()

    def execute(
        self,
        event_id: int,
        sender_id: int,
        content: str = "",
        media_url: Optional[str] = None,
        message_tags: Optional[List[str]] = None
    ) -> UseCaseResult:
        """
        执行添加事件消息用例

        Args:
            event_id: 事件ID
            sender_id: 发送者ID
            content: 消息内容
            media_url: 媒体文件URL
            message_tags: 回应标签数组

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

            if not sender_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='发送者ID不能为空'
                )

            # 至少要有文字内容、媒体文件或快捷指令
            if not content.strip() and not media_url and not message_tags:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='请至少提供文字内容、媒体文件或快捷指令'
                )

            # 2. 查询事件
            event = self.community_event_repository.find_by_id(event_id)
            if not event:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='事件不存在'
                )

            # 3. 验证事件状态（只有未关闭的事件才能添加消息）
            if event.status != 1:  # 1=pending
                return UseCaseResult(
                    status=UseCaseStatus.BUSINESS_ERROR,
                    message='事件已关闭，无法添加消息'
                )

            # 4. 验证发送者是否存在
            sender = self.user_repository.find_by_id(sender_id)
            if not sender:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='发送者不存在'
                )

            # 5. 确定消息类型
            message_type = 'text'
            if media_url:
                if media_url.endswith('.mp3') or media_url.endswith('.m4a'):
                    message_type = 'voice'
                elif media_url.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    message_type = 'image'

            # 6. 创建事件消息
            event_message = EventMessage(
                event_id=event_id,
                sender_id=sender_id,
                message_content=content.strip() if content else "",
                message_type=message_type,
                media_url=media_url,
                message_tags=message_tags or [],
                status=1
            )

            saved_message = self.event_message_repository.save(event_message)

            self.logger.info(f'添加事件消息成功: event_id={event_id}, message_id={saved_message.message_id}')

            # 7. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='添加事件消息成功',
                data={
                    'message_id': saved_message.message_id,
                    'event_id': saved_message.event_id,
                    'sender_id': saved_message.sender_id,
                    'message_content': saved_message.message_content,
                    'message_type': saved_message.message_type,
                    'media_url': saved_message.media_url,
                    'message_tags': saved_message.message_tags,
                    'created_at': saved_message.created_at.isoformat() if saved_message.created_at else None
                }
            )

        except Exception as e:
            self.logger.error(f'添加事件消息失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'添加事件消息失败: {str(e)}'
            )