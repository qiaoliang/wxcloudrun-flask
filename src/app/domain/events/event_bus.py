"""
事件总线

事件总线负责发布和订阅领域事件。
"""
from typing import Callable, Dict, List, Type
from collections import defaultdict
import logging

from app.domain.events.domain_event import DomainEvent

logger = logging.getLogger(__name__)


class EventBus:
    """
    事件总线

    使用观察者模式实现事件的发布和订阅。
    """

    _instance = None
    _handlers: Dict[Type[DomainEvent], List[Callable]] = defaultdict(list)

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def subscribe(cls, event_type: Type[DomainEvent], handler: Callable[[DomainEvent], None]) -> None:
        """
        订阅事件

        Args:
            event_type: 事件类型
            handler: 事件处理器
        """
        cls._handlers[event_type].append(handler)
        logger.info(f"订阅事件: {event_type.__name__}, 处理器: {handler.__name__}")

    @classmethod
    def unsubscribe(cls, event_type: Type[DomainEvent], handler: Callable[[DomainEvent], None]) -> bool:
        """
        取消订阅事件

        Args:
            event_type: 事件类型
            handler: 事件处理器

        Returns:
            是否取消成功
        """
        if handler in cls._handlers[event_type]:
            cls._handlers[event_type].remove(handler)
            logger.info(f"取消订阅事件: {event_type.__name__}, 处理器: {handler.__name__}")
            return True
        return False

    @classmethod
    def publish(cls, event: DomainEvent) -> None:
        """
        发布事件

        Args:
            event: 领域事件
        """
        event_type = type(event)
        handlers = cls._handlers.get(event_type, [])

        if not handlers:
            logger.warning(f"事件 {event_type.__name__} 没有订阅者")
            return

        logger.info(f"发布事件: {event_type.__name__}, 事件ID: {event.event_id}")

        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"处理事件 {event_type.__name__} 时出错: {str(e)}", exc_info=True)

    @classmethod
    def clear(cls) -> None:
        """清除所有订阅（主要用于测试）"""
        cls._handlers.clear()
        logger.info("清除所有事件订阅")

    @classmethod
    def get_subscribers_count(cls, event_type: Type[DomainEvent]) -> int:
        """
        获取事件的订阅者数量

        Args:
            event_type: 事件类型

        Returns:
            订阅者数量
        """
        return len(cls._handlers.get(event_type, []))