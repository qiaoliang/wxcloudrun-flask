"""
领域事件处理器基类

定义了事件处理器的标准接口和基础功能
"""
from abc import ABC, abstractmethod
from typing import Type, TypeVar
import logging

from .event import DomainEvent

logger = logging.getLogger(__name__)

E = TypeVar('E', bound=DomainEvent)


class EventHandler(ABC):
    """
    领域事件处理器基类

    所有事件处理器都应该继承此类并实现 handle 方法
    """

    def __init__(self):
        self.logger = logger

    @abstractmethod
    def handle(self, event: E) -> None:
        """
        处理领域事件

        Args:
            event: 领域事件实例
        """
        pass

    def can_handle(self, event: DomainEvent) -> bool:
        """
        检查是否可以处理该事件

        Args:
            event: 领域事件实例

        Returns:
            bool: 是否可以处理该事件
        """
        # 默认实现：检查事件类型是否匹配
        event_type = self.get_event_type()
        return isinstance(event, event_type)

    @staticmethod
    @abstractmethod
    def get_event_type() -> Type[DomainEvent]:
        """
        获取该处理器可以处理的事件类型

        Returns:
            Type[DomainEvent]: 事件类型
        """
        pass

    async def handle_async(self, event: E) -> None:
        """
        异步处理领域事件（可选实现）

        Args:
            event: 领域事件实例
        """
        # 默认实现：同步调用 handle 方法
        self.handle(event)