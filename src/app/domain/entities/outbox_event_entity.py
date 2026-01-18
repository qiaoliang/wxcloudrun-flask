"""
Outbox 事件领域实体

用于 Outbox 模式中的事件跟踪，确保事件的可靠投递。
提供事件状态管理、重试计算等功能。
"""
from datetime import datetime, timedelta
from app.domain.enums.outbox_status import OutboxStatus

class OutboxEventEntity:
    """Outbox 事件领域实体"""

    def __init__(self, event_type: str, payload: dict):
        """
        初始化 Outbox 事件实体

        Args:
            event_type: 事件类型（如 CheckinCompletedEvent）
            payload: 事件数据（字典格式）
        """
        self.id = None
        self.event_type = event_type
        self.payload = payload
        self.status = OutboxStatus.PENDING
        self.retry_count = 0
        self.created_at = datetime.now()
        self.published_at = None
        self.next_retry_at = datetime.now()

    def mark_as_published(self) -> None:
        """标记为已发布"""
        self.status = OutboxStatus.PUBLISHED
        self.published_at = datetime.now()

    def calculate_next_retry(self) -> None:
        """计算下次重试时间（指数退避）"""
        delay = min(2 ** self.retry_count, 60)  # 最多 60 秒
        self.next_retry_at = datetime.now() + timedelta(seconds=delay)
        self.retry_count += 1

    def should_retry(self) -> bool:
        """判断是否应该重试"""
        return self.retry_count < 5
