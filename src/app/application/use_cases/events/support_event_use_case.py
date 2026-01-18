"""
支持事件用例
"""
import logging
from datetime import datetime
from typing import Optional

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.domain.events.event_bus import EventBus
from app.domain.events.community_events import EventSupportedEvent
from app.domain.entities.community_event_entity import CommunityEventEntity
from app.domain.aggregates.community_event_aggregate import CommunityEventAggregate
from database.flask_models import EventMessage


class SupportEventUseCase(BaseUseCase):
    """支持事件用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.user_repository = RepositoryFactory.get_user_repository()
        self.community_event_repository = RepositoryFactory.get_community_event_repository()
        self.event_message_repository = RepositoryFactory.get_event_message_repository()
        self.community_staff_repository = RepositoryFactory.get_community_staff_repository()
        self.event_bus = EventBus()

    @transactional


    def execute(
        self,
        sender_id: int,
        event_id: int,
        message_content: str = ""
    ) -> UseCaseResult:
        """
        执行支持事件用例

        Args:
            sender_id: 发送者ID
            event_id: 事件ID
            message_content: 消息内容

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

            # 2. 验证发送者是否存在
            sender = self.user_repository.find_by_id(sender_id)
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

            # 4. 验证发送者是否为社区工作人员
            is_staff = self.community_staff_repository.exists(event.community_id, sender_id)
            if not is_staff:
                return UseCaseResult(
                    status=UseCaseStatus.FORBIDDEN,
                    message='无权限进行应援操作'
                )

            # 5. 检查是否已经应援过
            existing_messages = self.event_message_repository.find_active_by_event_id(event_id)
            for msg in existing_messages:
                if msg.sender_id == sender_id:
                    return UseCaseResult(
                        status=UseCaseStatus.BUSINESS_ERROR,
                        message='您已经应援过该事件'
                    )

            # 6. 创建事件聚合根并添加消息
            event_entity = CommunityEventEntity(event)
            event_aggregate = CommunityEventAggregate(event_entity)

            # 在聚合根中添加消息（业务规则在聚合根内验证）
            try:
                from app.domain.entities.event_message_entity import EventMessageEntity
                # 创建 EventMessage 对象
                message_obj = EventMessage(
                    event_id=event_id,
                    sender_id=sender_id,
                    message_content=message_content,
                    message_type='text',
                    status=1,
                    created_at=datetime.now()
                )
                message_entity = EventMessageEntity(message_obj)
                event_aggregate.add_message(message_entity)
            except ValueError as e:
                return UseCaseResult(
                    status=UseCaseStatus.BUSINESS_ERROR,
                    message=str(e)
                )

            # 7. 创建应援记录
            support = EventMessage(
                event_id=event_id,
                sender_id=sender_id,
                message_content=message_content,
                message_type='text',
                status=1,  # 有效
                created_at=datetime.now()
            )

            saved_support = self.event_message_repository.save(support)

            self.logger.info(f"用户{sender_id}对事件{event_id}进行了应援")

            # 8. 发布领域事件
            self.event_bus.publish(EventSupportedEvent(
                event_id=event_id,
                community_id=event.community_id,
                supporter_id=sender_id,
                message_content=message_content
            ))

            # 9. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='应援成功',
                data={
                    'support': {
                        'message_id': saved_support.message_id,
                        'event_id': saved_support.event_id,
                        'sender_id': saved_support.sender_id,
                        'message_content': saved_support.message_content,
                        'status': saved_support.status,
                        'created_at': saved_support.created_at.isoformat() if saved_support.created_at else None
                    }
                }
            )

        except ValueError as e:
            self.logger.error(f'创建应援失败: {str(e)}')
            return UseCaseResult(
                status=UseCaseStatus.BUSINESS_ERROR,
                message=str(e)
            )
        except Exception as e:
            self.logger.error(f'创建应援失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'应援失败: {str(e)}'
            )