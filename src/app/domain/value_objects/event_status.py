"""
事件状态值对象
"""
from dataclasses import dataclass
from enum import Enum


class EventStatus(Enum):
    """事件状态枚举"""
    PENDING = 1     # 待处理
    RESOLVED = 2    # 已解决
    CANCELLED = 3   # 已取消

    @property
    def name(self) -> str:
        """获取事件状态名称"""
        return {
            EventStatus.PENDING: "待处理",
            EventStatus.RESOLVED: "已解决",
            EventStatus.CANCELLED: "已取消"
        }.get(self, "未知状态")


@dataclass(frozen=True)
class CommunityEventStatus:
    """社区事件状态值对象"""
    value: EventStatus

    @classmethod
    def from_int(cls, value: int) -> 'CommunityEventStatus':
        """从整数值创建事件状态"""
        try:
            return cls(EventStatus(value))
        except ValueError:
            raise ValueError(f"无效的事件状态: {value}")

    @property
    def status_id(self) -> int:
        """获取状态ID"""
        return self.value.value

    @property
    def status_name(self) -> str:
        """获取状态名称"""
        return self.value.name

    def is_pending(self) -> bool:
        """是否待处理"""
        return self.value == EventStatus.PENDING

    def is_resolved(self) -> bool:
        """是否已解决"""
        return self.value == EventStatus.RESOLVED

    def is_cancelled(self) -> bool:
        """是否已取消"""
        return self.value == EventStatus.CANCELLED

    def __str__(self) -> str:
        return self.status_name

    def __eq__(self, other) -> bool:
        if not isinstance(other, CommunityEventStatus):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)