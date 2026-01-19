"""
增强的事件总线 - 支持 Outbox 降级模式

这个事件总线专门用于 Outbox 模式，与基础的事件总线不同：
1. 支持同步发布失败时自动降级到 Outbox
2. 支持从 Outbox 重新发布事件
3. 确保事件不丢失的可靠投递

与基础 EventBus 的区别：
- EventBus: 轻量级内存事件总线，不支持持久化
- EnhancedEventBus: 支持 Outbox 降级的事务性事件总线
"""
from typing import Dict, List, Callable, Any
from datetime import datetime
from app.domain.events.domain_event import DomainEvent
from app.domain.entities.outbox_event_entity import OutboxEventEntity
from app.domain.repositories.outbox_repository import OutboxRepository
from app.domain.enums.outbox_status import OutboxStatus
import logging

logger = logging.getLogger(__name__)


class EnhancedEventBus:
    """
    增强的事件总线

    支持通过 Outbox 模式确保事件的可靠投递。
    当同步发布失败时，事件会自动保存到 Outbox 以供后续重试。
    """

    def __init__(self, outbox_repository: OutboxRepository):
        """
        初始化增强事件总线

        Args:
            outbox_repository: Outbox 仓储实例
        """
        self._handlers: Dict[str, List[Callable]] = {}
        self._outbox_repo = outbox_repository

    def subscribe(self, event_type: str, handler: Callable) -> None:
        """
        订阅事件

        Args:
            event_type: 事件类型名称（如 'CheckinCompletedEvent'）
            handler: 事件处理函数，接收 DomainEvent 作为参数
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.debug(f"Handler subscribed to {event_type}")

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """
        取消订阅事件

        Args:
            event_type: 事件类型名称
            handler: 要取消的事件处理函数
        """
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
                logger.debug(f"Handler unsubscribed from {event_type}")
            except ValueError:
                logger.warning(f"Handler not found in {event_type} subscribers")

    def publish_with_fallback(self, event: DomainEvent) -> None:
        """
        发布事件（支持 Outbox 降级）

        首先尝试同步发布到所有订阅者。
        如果任何处理器失败，将事件保存到 Outbox 以供后续重试。

        Args:
            event: 领域事件实例
        """
        event_type = event.event_type
        handlers = self._handlers.get(event_type, [])

        if not handlers:
            logger.debug(f"No handlers for {event_type}, skipping")
            return

        try:
            # 尝试同步发布
            for handler in handlers:
                handler(event)

            logger.info(f"Event {event_type} published successfully to {len(handlers)} handler(s)")

        except Exception as e:
            # 同步发布失败，降级到 Outbox
            logger.warning(
                f"Failed to publish {event_type} synchronously: {e}. "
                f"Falling back to Outbox pattern."
            )
            self._save_to_outbox(event)

    def publish_from_outbox(self, outbox_event: OutboxEventEntity) -> bool:
        """
        从 Outbox 重新发布事件

        用于后台任务处理 Outbox 中的待发布事件。

        Args:
            outbox_event: Outbox 事件实体

        Returns:
            bool: 发布是否成功
        """
        event_type = outbox_event.event_type
        handlers = self._handlers.get(event_type, [])

        if not handlers:
            logger.warning(f"No handlers for {event_type}, cannot publish from Outbox")
            return False

        try:
            # 从 OutboxEvent 重建 DomainEvent
            domain_event = self._reconstruct_domain_event(outbox_event)

            # 同步发布
            for handler in handlers:
                handler(domain_event)

            logger.info(f"Event {event_type} published from Outbox successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to publish {event_type} from Outbox: {e}")
            # 更新 OutboxEvent 的重试信息
            outbox_event.calculate_next_retry()
            if not outbox_event.should_retry():
                logger.error(f"Event {outbox_event.id} exceeded max retries")
                outbox_event.status = OutboxStatus.FAILED
            return False

    def _save_to_outbox(self, event: DomainEvent) -> None:
        """
        将事件保存到 Outbox

        Args:
            event: 领域事件
        """
        # 将 datetime 对象转换为字符串
        def serialize_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        # 手动序列化 data 字典中的 datetime 对象
        serialized_data = {}
        for key, value in event.data.items():
            if isinstance(value, datetime):
                serialized_data[key] = value.isoformat()
            else:
                serialized_data[key] = value

        payload = {
            'event_id': event.event_id,
            'aggregate_id': event.aggregate_id,
            'data': serialized_data,
            'occurred_on': event.occurred_on.isoformat()
        }

        outbox_event = OutboxEventEntity(
            event_type=event.event_type,
            payload=payload
        )

        self._outbox_repo.save(outbox_event)
        logger.info(f"Event {event.event_type} saved to Outbox for retry")

    def _reconstruct_domain_event(self, outbox_event: OutboxEventEntity) -> DomainEvent:
        """
        从 OutboxEvent 重建 DomainEvent

        注意：这是一个简化版本，实际应用中可能需要根据事件类型动态重建

        Args:
            outbox_event: Outbox 事件实体

        Returns:
            DomainEvent: 重建的领域事件
        """
        payload = outbox_event.payload

        # 根据事件类型创建相应的 DomainEvent
        # 这里需要导入所有可能的事件类型
        from app.domain.events.checkin_events import (
            CheckinCompletedEvent,
            CheckinMissedEvent,
            CheckinCancelledEvent,
            CheckinRuleCreatedEvent,
            CheckinRuleUpdatedEvent,
            CheckinRuleDeletedEvent,
            CheckinRuleEnabledEvent,
            CheckinRuleDisabledEvent
        )

        event_classes = {
            'CheckinCompletedEvent': CheckinCompletedEvent,
            'CheckinMissedEvent': CheckinMissedEvent,
            'CheckinCancelledEvent': CheckinCancelledEvent,
            'CheckinRuleCreatedEvent': CheckinRuleCreatedEvent,
            'CheckinRuleUpdatedEvent': CheckinRuleUpdatedEvent,
            'CheckinRuleDeletedEvent': CheckinRuleDeletedEvent,
            'CheckinRuleEnabledEvent': CheckinRuleEnabledEvent,
            'CheckinRuleDisabledEvent': CheckinRuleDisabledEvent,
        }

        event_class = event_classes.get(outbox_event.event_type)
        if not event_class:
            raise ValueError(f"Unknown event type: {outbox_event.event_type}")

        # 从 payload 中提取数据
        data = payload.get('data', {})
        aggregate_id = payload.get('aggregate_id')

        # 根据事件类型重建
        if outbox_event.event_type == 'CheckinCompletedEvent':
            return CheckinCompletedEvent(
                record_id=data.get('record_id'),
                user_id=data.get('user_id'),
                rule_id=data.get('rule_id'),
                checkin_time=data.get('checkin_time')
            )
        elif outbox_event.event_type == 'CheckinMissedEvent':
            return CheckinMissedEvent(
                record_id=data.get('record_id'),
                user_id=data.get('user_id'),
                rule_id=data.get('rule_id'),
                scheduled_time=data.get('scheduled_time')
            )
        elif outbox_event.event_type == 'CheckinCancelledEvent':
            return CheckinCancelledEvent(
                record_id=data.get('record_id'),
                user_id=data.get('user_id'),
                rule_id=data.get('rule_id'),
                reason=data.get('reason')
            )
        elif outbox_event.event_type == 'CheckinRuleCreatedEvent':
            return CheckinRuleCreatedEvent(
                rule_id=data.get('rule_id'),
                user_id=data.get('user_id'),
                rule_name=data.get('rule_name'),
                frequency_type=data.get('frequency_type')
            )
        elif outbox_event.event_type == 'CheckinRuleUpdatedEvent':
            return CheckinRuleUpdatedEvent(
                rule_id=data.get('rule_id'),
                user_id=data.get('user_id'),
                updated_fields=data.get('updated_fields')
            )
        elif outbox_event.event_type == 'CheckinRuleDeletedEvent':
            return CheckinRuleDeletedEvent(
                rule_id=data.get('rule_id'),
                user_id=data.get('user_id')
            )
        elif outbox_event.event_type == 'CheckinRuleEnabledEvent':
            return CheckinRuleEnabledEvent(
                rule_id=data.get('rule_id'),
                user_id=data.get('user_id')
            )
        elif outbox_event.event_type == 'CheckinRuleDisabledEvent':
            return CheckinRuleDisabledEvent(
                rule_id=data.get('rule_id'),
                user_id=data.get('user_id')
            )
        else:
            raise ValueError(f"Cannot reconstruct event type: {outbox_event.event_type}")
