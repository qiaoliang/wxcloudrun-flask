"""
社区事件聚合根

社区事件聚合是社区事件相关的核心业务概念，包含事件本身及其关联的消息等。
"""
from typing import List, Optional

from app.domain.entities.community_event_entity import CommunityEventEntity
from app.domain.entities.event_message_entity import EventMessageEntity


class CommunityEventAggregate:
    """
    社区事件聚合根

    聚合边界：
    - CommunityEventEntity（社区事件实体）
    - EventMessageEntity（事件消息）

    业务不变性：
    - 事件必须有创建者
    - 事件必须属于一个社区
    - 事件状态转换必须符合业务规则
    - 事件消息必须属于一个事件
    - 只有事件创建者或社区工作人员可以添加消息
    """

    def __init__(self, event_entity: CommunityEventEntity):
        """
        初始化社区事件聚合根

        Args:
            event_entity: 社区事件实体
        """
        self._event = event_entity
        self._messages: List[EventMessageEntity] = []

    @property
    def event(self) -> CommunityEventEntity:
        """获取事件实体"""
        return self._event

    @property
    def messages(self) -> List[EventMessageEntity]:
        """获取事件消息列表"""
        return self._messages

    def add_message(self, message: EventMessageEntity) -> None:
        """
        添加事件消息

        Args:
            message: 事件消息实体

        Raises:
            ValueError: 如果消息不属于该事件或事件已关闭
        """
        if message.event_id != self._event.event_id:
            raise ValueError("消息不属于该事件")

        # 只有待处理的事件才能添加消息
        if not self._event.is_pending:
            raise ValueError("事件已关闭，无法添加消息")

        self._messages.append(message)

    def get_messages_by_sender(self, sender_id: int) -> List[EventMessageEntity]:
        """
        获取指定发送者的消息

        Args:
            sender_id: 发送者ID

        Returns:
            消息列表
        """
        return [msg for msg in self._messages if msg.sender_id == sender_id]

    def get_messages_by_type(self, message_type: str) -> List[EventMessageEntity]:
        """
        获取指定类型的消息

        Args:
            message_type: 消息类型

        Returns:
            消息列表
        """
        return [msg for msg in self._messages if msg.message_type == message_type]

    def get_latest_message(self) -> Optional[EventMessageEntity]:
        """
        获取最新消息

        Returns:
            最新消息，如果没有则返回None
        """
        if not self._messages:
            return None
        return max(self._messages, key=lambda m: m.created_at)

    def get_message_count(self) -> int:
        """
        获取消息数量

        Returns:
            消息数量
        """
        return len(self._messages)

    def resolve(self, reason: str) -> None:
        """
        解决事件

        Args:
            reason: 解决原因
        """
        self._event.resolve(reason)

    def cancel(self, reason: str) -> None:
        """
        取消事件

        Args:
            reason: 取消原因
        """
        self._event.cancel(reason)

    def is_resolved(self) -> bool:
        """
        检查事件是否已解决

        Returns:
            是否已解决
        """
        return self._event.is_resolved()

    def is_cancelled(self) -> bool:
        """
        检查事件是否已取消

        Returns:
            是否已取消
        """
        return self._event.is_cancelled()

    def is_pending(self) -> bool:
        """
        检查事件是否待处理

        Returns:
            是否待处理
        """
        return self._event.is_pending()

    def can_be_supported(self, user_id: int, is_staff: bool) -> bool:
        """
        检查事件是否可以被支持

        Args:
            user_id: 用户ID
            is_staff: 是否是社区工作人员

        Returns:
            是否可以被支持
        """
        # 只有待处理的事件才能被支持
        if not self.is_pending():
            return False

        # 事件创建者不能支持自己的事件
        if user_id == self._event.creator_id:
            return False

        # 只有社区工作人员可以支持事件
        return is_staff

    def support(self, supporter_id: int) -> None:
        """
        支持事件

        Args:
            supporter_id: 支持者ID

        Raises:
            ValueError: 如果事件不能被支持
        """
        if not self.can_be_supported(supporter_id, is_staff=True):
            raise ValueError("该事件不能被支持")

        self._event.support(supporter_id)

    def __eq__(self, other) -> bool:
        if not isinstance(other, CommunityEventAggregate):
            return False
        return self._event == other._event

    def __hash__(self) -> int:
        return hash(self._event)