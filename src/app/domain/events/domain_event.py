"""
领域事件基类
"""
from abc import ABC
from datetime import datetime
from typing import Any, Dict
import uuid


class DomainEvent(ABC):
    """
    领域事件基类

    所有领域事件都应该继承此类。
    """

    def __init__(self, aggregate_id: Any, data: Dict[str, Any] = None):
        """
        初始化领域事件

        Args:
            aggregate_id: 聚合根ID
            data: 事件数据
        """
        self._event_id = str(uuid.uuid4())
        self._aggregate_id = aggregate_id
        self._occurred_on = datetime.now()
        self._data = data or {}

    @property
    def event_id(self) -> str:
        """获取事件ID"""
        return self._event_id

    @property
    def aggregate_id(self) -> Any:
        """获取聚合根ID"""
        return self._aggregate_id

    @property
    def occurred_on(self) -> datetime:
        """获取事件发生时间"""
        return self._occurred_on

    @property
    def data(self) -> Dict[str, Any]:
        """获取事件数据"""
        return self._data

    @property
    def event_type(self) -> str:
        """获取事件类型"""
        return self.__class__.__name__

    def __repr__(self) -> str:
        return f"{self.event_type}(id={self._event_id}, aggregate_id={self._aggregate_id}, occurred_on={self._occurred_on})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, DomainEvent):
            return False
        return self._event_id == other._event_id

    def __hash__(self) -> int:
        return hash(self._event_id)