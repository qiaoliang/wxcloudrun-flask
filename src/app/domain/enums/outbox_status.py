"""
Outbox 事件状态枚举

用于 Outbox 模式中的事件状态跟踪，确保事件的可靠投递。

状态转换流程：
- PENDING -> PUBLISHED (成功)
- PENDING -> FAILED (失败)
- FAILED -> PENDING (重试)
"""
from enum import Enum


class OutboxStatus(Enum):
    """Outbox 事件状态枚举"""
    PENDING = 'pending'      # 待处理
    PUBLISHED = 'published'  # 已发布
    FAILED = 'failed'        # 发布失败
