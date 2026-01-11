"""
社区事件领域实体

封装社区事件相关的业务逻辑。
"""
from typing import Optional
from datetime import datetime

from database.flask_models import CommunityEvent


class CommunityEventEntity:
    """社区事件领域实体"""

    def __init__(self, event: CommunityEvent):
        """
        初始化社区事件领域实体

        Args:
            event: SQLAlchemy CommunityEvent 模型实例
        """
        self._event = event

    @property
    def event(self) -> CommunityEvent:
        """获取底层的 SQLAlchemy CommunityEvent 模型"""
        return self._event

    @property
    def event_id(self) -> int:
        """获取事件ID"""
        return self._event.event_id

    @property
    def community_id(self) -> int:
        """获取社区ID"""
        return self._event.community_id

    @property
    def event_type(self) -> str:
        """获取事件类型"""
        return self._event.event_type

    @property
    def status(self) -> int:
        """获取事件状态"""
        return self._event.status

    @property
    def is_pending(self) -> bool:
        """是否待处理"""
        return self._event.status == 1

    @property
    def is_resolved(self) -> bool:
        """是否已解决"""
        return self._event.status == 2

    @property
    def is_cancelled(self) -> bool:
        """是否已取消"""
        return self._event.status == 3

    @property
    def created_by(self) -> int:
        """获取创建者ID"""
        return self._event.created_by

    @property
    def target_user_id(self) -> int:
        """获取目标用户ID"""
        return self._event.target_user_id

    def resolve(self, reason: str, resolved_by: int) -> None:
        """
        解决事件

        Args:
            reason: 解决原因
            resolved_by: 解决者ID
        """
        self._event.status = 2
        self._event.resolution_reason = reason[:500] if reason else None
        self._event.resolved_by = resolved_by
        self._event.resolved_at = datetime.now()
        self._event.updated_at = datetime.now()

    def cancel(self) -> None:
        """取消事件"""
        self._event.status = 3
        self._event.updated_at = datetime.now()

    def add_support_message(self, sender_id: int, message: str) -> None:
        """
        添加支持消息

        Args:
            sender_id: 发送者ID
            message: 消息内容
        """
        from database.flask_models import EventMessage, db

        event_message = EventMessage(
            event_id=self._event.event_id,
            sender_id=sender_id,
            message=message[:1000] if message else None
        )
        db.session.add(event_message)
        self._event.updated_at = datetime.now()

    def get_support_count(self) -> int:
        """
        获取支持数量

        Returns:
            支持消息数量
        """
        return len(self._event.messages)

    def is_call_for_help(self) -> bool:
        """
        是否为求救事件

        Returns:
            bool: 是否为求救事件
        """
        return self._event.event_type == 'call_for_help'

    def is_supporting(self) -> bool:
        """
        是否为支持事件

        Returns:
            bool: 是否为支持事件
        """
        return self._event.event_type == 'supporting'

    def __eq__(self, other) -> bool:
        if not isinstance(other, CommunityEventEntity):
            return False
        return self._event.event_id == other._event.event_id

    def __hash__(self) -> int:
        return hash(self._event.event_id)