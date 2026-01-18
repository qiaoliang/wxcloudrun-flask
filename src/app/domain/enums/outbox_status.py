from enum import Enum


class OutboxStatus(Enum):
    """Outbox 事件状态枚举"""
    PENDING = 'pending'      # 待处理
    PUBLISHED = 'published'  # 已发布
    FAILED = 'failed'        # 发布失败
