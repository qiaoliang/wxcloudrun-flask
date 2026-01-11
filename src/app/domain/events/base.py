"""
领域事件基类
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict
from uuid import uuid4


@dataclass
class DomainEvent:
    """领域事件基类"""

    event_id: str = None
    occurred_on: datetime = None
    event_type: str = None

    def __post_init__(self):
        """初始化事件ID和发生时间"""
        if self.event_id is None:
            self.event_id = str(uuid4())
        if self.occurred_on is None:
            self.occurred_on = datetime.now()
        if self.event_type is None:
            self.event_type = self.__class__.__name__

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'occurred_on': self.occurred_on.isoformat()
        }