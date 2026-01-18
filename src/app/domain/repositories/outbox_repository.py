from abc import ABC, abstractmethod
from typing import List
from app.domain.entities.outbox_event_entity import OutboxEventEntity
from app.domain.enums.outbox_status import OutboxStatus

class OutboxRepository(ABC):
    """Outbox 仓储接口"""

    @abstractmethod
    def save(self, event: OutboxEventEntity) -> OutboxEventEntity:
        """
        保存事件到 Outbox

        Args:
            event: Outbox 事件实体

        Returns:
            OutboxEventEntity: 保存后的实体（带 ID）
        """
        pass

    @abstractmethod
    def find_pending_events(self, limit: int = 100) -> List[OutboxEventEntity]:
        """
        查找待处理事件

        Args:
            limit: 最大返回数量

        Returns:
            List[OutboxEventEntity]: 待处理事件列表
        """
        pass

    @abstractmethod
    def update_status(self, event_id: int, status: OutboxStatus) -> None:
        """
        更新事件状态

        Args:
            event_id: 事件 ID
            status: 新状态
        """
        pass
