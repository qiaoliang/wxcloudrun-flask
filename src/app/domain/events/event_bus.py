"""
领域事件总线

负责发布和订阅领域事件。
"""
import logging
from typing import Callable, List, Dict, Type
from .base import DomainEvent


class EventBus:
    """领域事件总线"""

    def __init__(self):
        self._handlers: Dict[Type[DomainEvent], List[Callable]] = {}
        self.logger = logging.getLogger(__name__)

    def subscribe(self, event_type: Type[DomainEvent], handler: Callable) -> None:
        """
        订阅领域事件

        Args:
            event_type: 事件类型
            handler: 事件处理器
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        self.logger.info(f"订阅事件: {event_type.__name__}, 处理器: {handler.__name__}")

    def unsubscribe(self, event_type: Type[DomainEvent], handler: Callable) -> None:
        """
        取消订阅领域事件

        Args:
            event_type: 事件类型
            handler: 事件处理器
        """
        if event_type in self._handlers:
            if handler in self._handlers[event_type]:
                self._handlers[event_type].remove(handler)
                self.logger.info(f"取消订阅事件: {event_type.__name__}, 处理器: {handler.__name__}")

    def publish(self, event: DomainEvent) -> None:
        """
        发布领域事件

        Args:
            event: 领域事件
        """
        event_type = type(event)
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                try:
                    handler(event)
                except Exception as e:
                    self.logger.error(f"处理事件失败: {event_type.__name__}, 处理器: {handler.__name__}, 错误: {str(e)}")
        else:
            self.logger.debug(f"没有处理器订阅事件: {event_type.__name__}")

    def clear(self) -> None:
        """清除所有事件处理器"""
        self._handlers.clear()
        self.logger.info("清除所有事件处理器")


# 全局事件总线实例
event_bus = EventBus()