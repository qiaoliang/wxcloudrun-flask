"""
事件类型值对象
"""
from dataclasses import dataclass
from enum import Enum


class EventType(Enum):
    """事件类型枚举"""
    CALL_FOR_HELP = "call_for_help"  # 求救
    SUPPORTING = "supporting"        # 支持

    @property
    def name(self) -> str:
        """获取事件类型名称"""
        return {
            EventType.CALL_FOR_HELP: "求救",
            EventType.SUPPORTING: "支持"
        }.get(self.value, "未知事件")


@dataclass(frozen=True)
class CommunityEventType:
    """社区事件类型值对象"""
    value: EventType

    @classmethod
    def from_string(cls, value: str) -> 'CommunityEventType':
        """从字符串创建事件类型"""
        try:
            return cls(EventType(value))
        except ValueError:
            raise ValueError(f"无效的事件类型: {value}")

    @property
    def event_type(self) -> str:
        """获取事件类型字符串"""
        return self.value.value

    @property
    def event_type_name(self) -> str:
        """获取事件类型名称"""
        return self.value.name

    def is_call_for_help(self) -> bool:
        """是否为求救事件"""
        return self.value == EventType.CALL_FOR_HELP

    def is_supporting(self) -> bool:
        """是否为支持事件"""
        return self.value == EventType.SUPPORTING

    def __str__(self) -> str:
        return self.event_type_name

    def __eq__(self, other) -> bool:
        if not isinstance(other, CommunityEventType):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)