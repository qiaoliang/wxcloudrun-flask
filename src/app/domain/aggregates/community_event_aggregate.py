"""
社区事件聚合根

社区事件聚合是社区事件相关的核心业务概念，包含事件本身及其关联的支持消息。
"""
from typing import List, Optional

from app.domain.entities.community_event_entity import CommunityEventEntity


class CommunityEventAggregate:
    """
    社区事件聚合根

    聚合边界：
    - CommunityEventEntity（社区事件实体）
    - EventMessage（事件消息）

    业务不变性：
    - 事件必须关联到一个有效的社区
    - 事件必须有明确的目标用户
    - 事件的状态转换必须符合业务规则
    - 只有相关人员才能支持事件
    """

    def __init__(self, event_entity: CommunityEventEntity):
        """
        初始化社区事件聚合根

        Args:
            event_entity: 社区事件实体
        """
        self._event = event_entity
        self._messages: List[dict] = []

    @property
    def event(self) -> CommunityEventEntity:
        """获取社区事件实体"""
        return self._event

    @property
    def messages(self) -> List[dict]:
        """获取事件消息列表"""
        return self._messages

    def add_message(self, sender_id: int, message: str) -> None:
        """
        添加支持消息

        Args:
            sender_id: 发送者ID
            message: 消息内容
        """
        self._messages.append({
            'sender_id': sender_id,
            'message': message,
            'created_at': datetime.now()
        })

    def get_messages_by_sender(self, sender_id: int) -> List[dict]:
        """
        获取指定发送者的消息

        Args:
            sender_id: 发送者ID

        Returns:
            消息列表
        """
        return [msg for msg in self._messages if msg['sender_id'] == sender_id]

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

    def get_support_count(self) -> int:
        """
        获取支持人数

        Returns:
            支持人数
        """
        return len(self._messages)

    def __eq__(self, other) -> bool:
        if not isinstance(other, CommunityEventAggregate):
            return False
        return self._event == other._event

    def __hash__(self) -> int:
        return hash(self._event)