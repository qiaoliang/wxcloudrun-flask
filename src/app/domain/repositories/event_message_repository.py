"""
事件消息仓储接口
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from database.flask_models import EventMessage


class EventMessageRepository(ABC):
    """事件消息仓储接口"""

    @abstractmethod
    def find_by_id(self, message_id: int) -> Optional[EventMessage]:
        """根据ID查找事件消息"""
        pass

    @abstractmethod
    def find_by_event_id(self, event_id: int, limit: int = None) -> List[EventMessage]:
        """根据事件ID查找消息"""
        pass

    @abstractmethod
    def find_by_sender_id(self, sender_id: int) -> List[EventMessage]:
        """根据发送者ID查找消息"""
        pass

    @abstractmethod
    def find_active_by_event_id(self, event_id: int) -> List[EventMessage]:
        """查找事件的有效消息"""
        pass

    @abstractmethod
    def save(self, message: EventMessage) -> EventMessage:
        """保存事件消息"""
        pass

    @abstractmethod
    def update(self, message: EventMessage) -> EventMessage:
        """更新事件消息"""
        pass

    @abstractmethod
    def delete(self, message_id: int) -> bool:
        """删除事件消息"""
        pass

    @abstractmethod
    def cancel(self, message_id: int) -> bool:
        """取消事件消息"""
        pass

    @abstractmethod
    def count_by_event_id(self, event_id: int) -> int:
        """统计事件消息数量"""
        pass

    @abstractmethod
    def count_active_by_event_id(self, event_id: int) -> int:
        """统计事件有效消息数量"""
        pass