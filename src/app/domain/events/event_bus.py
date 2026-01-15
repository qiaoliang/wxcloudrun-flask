"""
领域事件总线

管理领域事件的发布和订阅
"""
from typing import Dict, List, Type, Callable
import logging
from concurrent.futures import ThreadPoolExecutor
import threading

from .event import DomainEvent
from .event_handler import EventHandler, E

logger = logging.getLogger(__name__)


class EventBus:
    """
    领域事件总线

    负责事件的发布和订阅管理
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """
        单例模式实现
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """
        初始化事件总线
        """
        if not hasattr(self, '_initialized'):
            self._handlers: Dict[Type[DomainEvent], List[EventHandler]] = {}
            self._executor = ThreadPoolExecutor(max_workers=10)
            self._initialized = True
            self.logger = logger

    def subscribe(self, handler: EventHandler) -> None:
        """
        订阅事件处理器

        Args:
            handler: 事件处理器实例
        """
        event_type = handler.get_event_type()
        if event_type not in self._handlers:
            self._handlers[event_type] = []

        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)
            self.logger.info(f"已订阅事件处理器: {handler.__class__.__name__} -> {event_type.__name__}")

    def unsubscribe(self, handler: EventHandler) -> None:
        """
        取消订阅事件处理器

        Args:
            handler: 事件处理器实例
        """
        event_type = handler.get_event_type()
        if event_type in self._handlers:
            if handler in self._handlers[event_type]:
                self._handlers[event_type].remove(handler)
                self.logger.info(f"已取消订阅事件处理器: {handler.__class__.__name__}")

    def publish(self, event: DomainEvent) -> None:
        """
        发布领域事件（同步）

        Args:
            event: 领域事件实例
        """
        event_type = type(event)
        if event_type in self._handlers:
            self.logger.info(f"发布事件: {event_type.__name__}")
            for handler in self._handlers[event_type]:
                try:
                    handler.handle(event)
                except Exception as e:
                    self.logger.error(f"处理事件失败: {event_type.__name__}, 处理器: {handler.__class__.__name__}, 错误: {e}")
        else:
            self.logger.warning(f"没有处理器订阅事件: {event_type.__name__}")

    def publish_async(self, event: DomainEvent) -> None:
        """
        发布领域事件（异步）

        Args:
            event: 领域事件实例
        """
        self._executor.submit(self.publish, event)

    def publish_batch(self, events: List[DomainEvent]) -> None:
        """
        批量发布领域事件

        Args:
            events: 领域事件列表
        """
        for event in events:
            self.publish(event)

    def publish_batch_async(self, events: List[DomainEvent]) -> None:
        """
        批量异步发布领域事件

        Args:
            events: 领域事件列表
        """
        for event in events:
            self._executor.submit(self.publish, event)

    def clear(self) -> None:
        """
        清除所有订阅
        """
        self._handlers.clear()
        self.logger.info("已清除所有事件处理器订阅")

    def get_handler_count(self, event_type: Type[DomainEvent]) -> int:
        """
        获取指定事件的处理器数量

        Args:
            event_type: 事件类型

        Returns:
            int: 处理器数量
        """
        if event_type in self._handlers:
            return len(self._handlers[event_type])
        return 0

    def shutdown(self) -> None:
        """
        关闭事件总线
        """
        self._executor.shutdown(wait=True)
        self.logger.info("事件总线已关闭")


# 全局事件总线实例
event_bus = EventBus()