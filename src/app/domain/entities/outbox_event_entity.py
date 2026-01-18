from datetime import datetime, timedelta
from app.domain.enums.outbox_status import OutboxStatus

class OutboxEventEntity:
    """Outbox 事件领域实体"""

    def __init__(self, event_type: str, payload: dict):
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
