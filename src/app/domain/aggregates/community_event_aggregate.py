"""
社区事件聚合根

社区事件聚合是社区事件相关的核心业务概念，包含事件本身及其关联的支持消息。
"""
from typing import List, Optional
from datetime import datetime

from app.domain.entities.community_event_entity import CommunityEventEntity
from app.domain.events.event_bus import EventBus


class CommunityEventAggregate:
    """
    社区事件聚合根

    聚合边界：
    - CommunityEventEntity（社区事件实体）
    - EventMessage（事件消息）

    业务不变性：
    - 事件必须关联到一个有效的社区
    - 事件必须有明确的目标用户（对于 call_for_help 类型）
    - 事件的状态转换必须符合业务规则
    - 只有相关人员才能支持事件
    - 事件关闭后不能再添加消息
    """

    def __init__(self, event_entity: CommunityEventEntity, event_bus: EventBus = None):
        """
        初始化社区事件聚合根

        Args:
            event_entity: 社区事件实体
            event_bus: 事件总线（用于发布领域事件）
        """
        self._event = event_entity
        self._messages: List[dict] = []
        self._event_bus = event_bus or EventBus()

    @property
    def event(self) -> CommunityEventEntity:
        """获取社区事件实体"""
        return self._event

    @property
    def messages(self) -> List[dict]:
        """获取事件消息列表"""
        return self._messages

    def add_message(self, sender_id: int, message: str, message_type: str = 'text',
                    media_url: str = None, message_tags: List[str] = None) -> None:
        """
        添加支持消息

        Args:
            sender_id: 发送者ID
            message: 消息内容
            message_type: 消息类型
            media_url: 媒体URL
            message_tags: 消息标签
        """
        # 检查事件是否已关闭
        if self._event.status != 1:
            raise ValueError("事件已关闭，无法添加消息")

        new_message = {
            'sender_id': sender_id,
            'message': message,
            'message_type': message_type,
            'media_url': media_url,
            'message_tags': message_tags or [],
            'created_at': datetime.now()
        }

        self._messages.append(new_message)

        # 发布事件消息添加领域事件
        from app.domain.events.community_events import EventMessageAddedEvent
        self._event_bus.publish(EventMessageAddedEvent(
            event_id=self._event.event_id,
            sender_id=sender_id,
            message_type=message_type
        ))

    def get_messages_by_sender(self, sender_id: int) -> List[dict]:
        """
        获取指定发送者的消息

        Args:
            sender_id: 发送者ID

        Returns:
            消息列表
        """
        return [msg for msg in self._messages if msg['sender_id'] == sender_id]

    def resolve(self, reason: str, resolved_by: int) -> None:
        """
        解决事件

        Args:
            reason: 解决原因
            resolved_by: 解决者ID
        """
        if self._event.status != 1:
            raise ValueError("事件已关闭，无法再次关闭")

        self._event.resolve(reason)

        # 发布事件关闭领域事件
        from app.domain.events.community_events import EventClosedEvent
        self._event_bus.publish(EventClosedEvent(
            event_id=self._event.event_id,
            community_id=self._event.community_id,
            resolved_by=resolved_by,
            closure_reason=reason
        ))

    def cancel(self, reason: str, cancelled_by: int) -> None:
        """
        取消事件

        Args:
            reason: 取消原因
            cancelled_by: 取消者ID
        """
        if self._event.status != 1:
            raise ValueError("事件已关闭，无法再次关闭")

        self._event.cancel(reason)

        # 发布事件取消领域事件
        from app.domain.events.community_events import EventCancelledEvent
        self._event_bus.publish(EventCancelledEvent(
            event_id=self._event.event_id,
            community_id=self._event.community_id,
            cancelled_by=cancelled_by,
            cancellation_reason=reason
        ))

    def update_location(self, location: str, location_lat: float = None,
                       location_lon: float = None) -> None:
        """
        更新事件位置

        Args:
            location: 位置描述
            location_lat: 纬度
            location_lon: 经度
        """
        if self._event.status != 1:
            raise ValueError("事件已关闭，无法更新位置")

        self._event.location = location
        if location_lat is not None:
            self._event.location_lat = location_lat
        if location_lon is not None:
            self._event.location_lon = location_lon

        # 发布事件位置更新领域事件
        from app.domain.events.community_events import EventLocationUpdatedEvent
        self._event_bus.publish(EventLocationUpdatedEvent(
            event_id=self._event.event_id,
            community_id=self._event.community_id,
            location=location,
            location_lat=location_lat,
            location_lon=location_lon
        ))

    def get_support_count(self) -> int:
        """
        获取支持人数

        Returns:
            支持人数
        """
        return len(self._messages)

    def is_pending(self) -> bool:
        """
        事件是否待处理

        Returns:
            是否待处理
        """
        return self._event.status == 1

    def is_resolved(self) -> bool:
        """
        事件是否已解决

        Returns:
            是否已解决
        """
        return self._event.status == 2

    def is_cancelled(self) -> bool:
        """
        事件是否已取消

        Returns:
            是否已取消
        """
        return self._event.status == 3

    def __eq__(self, other) -> bool:
        if not isinstance(other, CommunityEventAggregate):
            return False
        return self._event == other._event

    def __hash__(self) -> int:
        return hash(self._event)